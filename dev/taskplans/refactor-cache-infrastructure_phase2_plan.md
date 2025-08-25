# Phase 2 Implementation Plan: AI Cache Refactoring

## Overview
**Scope:** Refactor AIResponseCache to extend GenericRedisCache while maintaining all AI-specific features and ensuring no functionality is lost.

**Dependencies:** Requires completed Phase 1 (GenericRedisCache with memory cache integration, CacheKeyGenerator extraction, security framework, and migration tools)

**Duration:** 4-5 weeks

## Current State After Phase 1
After Phase 1 completion, we will have:
- ✅ `GenericRedisCache` with Redis operations, L1 memory cache, compression, security, monitoring
- ✅ `CacheKeyGenerator` as standalone component with performance monitoring
- ✅ `RedisCacheSecurityManager` for secure connections
- ✅ `CacheMigrationManager` for safe data transitions
- ✅ `CachePerformanceBenchmark` for validation
- ✅ Backwards compatibility layer maintained

## Phase 2 Deliverables

### 1. Comprehensive Parameter Mapping Analysis
**New file**: `backend/app/infrastructure/cache/parameter_mapping.py`

**Parameter Resolution Strategy:**
```python
class CacheParameterMapper:
    """Maps AI-specific parameters to GenericRedisCache parameters."""
    
    @staticmethod
    def map_ai_to_generic_params(ai_params: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Separate AI-specific params from generic Redis params."""
        generic_params = {
            'redis_url': ai_params.get('redis_url'),
            'default_ttl': ai_params.get('default_ttl'),
            'compression_threshold': ai_params.get('compression_threshold'),
            'compression_level': ai_params.get('compression_level'),
            'memory_cache_size': ai_params.get('memory_cache_size', 100),
            'performance_monitor': ai_params.get('performance_monitor'),
            'redis_auth': ai_params.get('redis_auth'),
            'use_tls': ai_params.get('use_tls', False)
        }
        
        ai_specific_params = {
            'text_hash_threshold': ai_params.get('text_hash_threshold', 1000),
            'hash_algorithm': ai_params.get('hash_algorithm', hashlib.sha256),
            'text_size_tiers': ai_params.get('text_size_tiers'),
            'operation_ttls': ai_params.get('operation_ttls')
        }
        
        return generic_params, ai_specific_params
    
    @staticmethod
    def validate_parameter_compatibility(ai_params: Dict[str, Any]) -> ValidationResult:
        """Validate AI parameters are compatible with generic cache."""
```

### 2. Refactor AIResponseCache Class Architecture
**Update**: `backend/app/infrastructure/cache/redis.py` → `backend/app/infrastructure/cache/redis_ai.py`

**Comprehensive Refactoring:**
```python
class AIResponseCache(GenericRedisCache):
    """AI-specialized cache extending GenericRedisCache.
    
    Inherits all Redis operations, memory cache management, compression,
    and security features while adding AI-specific optimizations.
    """
    
    def __init__(self, config: AIResponseCacheConfig):
        """Initialize with configuration object for cleaner interface."""
        
        # The CacheParameterMapper can now operate on the config object
        generic_params, ai_params = CacheParameterMapper.map_ai_to_generic_params(
            config.to_ai_cache_kwargs()
        )
        
        # Add AI-specific callbacks for composition over inheritance
        generic_params.update({
            'on_get_success': self._ai_get_success_callback,
            'on_get_miss': self._ai_get_miss_callback,
            'on_set_success': self._ai_set_success_callback,
        })
        
        # Initialize parent GenericRedisCache with AI callbacks
        super().__init__(**generic_params)
        
        # Setup AI-specific configuration
        self._setup_ai_configuration(**ai_params)
        
        # Initialize AI-specific components
        self._setup_ai_components()
        
    def _setup_ai_configuration(self, text_hash_threshold: int, hash_algorithm, 
                               text_size_tiers: Optional[Dict[str, int]], 
                               operation_ttls: Optional[Dict[str, int]]):
        """Setup AI-specific configuration."""
        self.operation_ttls = operation_ttls or {
            "summarize": 7200,    # 2 hours - summaries are stable
            "sentiment": 86400,   # 24 hours - sentiment rarely changes
            "key_points": 7200,   # 2 hours
            "questions": 3600,    # 1 hour - questions can vary
            "qa": 1800           # 30 minutes - context-dependent
        }
        
        self.text_size_tiers = text_size_tiers or {
            'small': 500,      # < 500 chars - cache with full text
            'medium': 5000,    # 500-5000 chars - cache with text hash
            'large': 50000,    # 5000-50000 chars - cache with content hash + metadata
        }
        
    def _setup_ai_components(self):
        """Initialize AI-specific components."""
        # Initialize optimized cache key generator with performance monitoring
        self.key_generator = CacheKeyGenerator(
            text_hash_threshold=self.text_hash_threshold,
            hash_algorithm=self.hash_algorithm,
            performance_monitor=self.performance_monitor
        )
        
        # AI-specific metrics tracking
        self.ai_metrics = {
            'cache_hits_by_operation': defaultdict(int),
            'cache_misses_by_operation': defaultdict(int),
            'text_tier_distribution': defaultdict(int),
            'operation_performance': defaultdict(list)
        }
```

### 3. Method Override Analysis and Implementation
**Detailed Method Override Strategy:**

#### Methods Inherited from GenericRedisCache (No Override Needed):
- `connect()` - Redis connection management
- `get()`, `set()`, `delete()` - Basic Redis operations  
- `exists()`, `get_ttl()`, `clear()` - Redis utilities
- `get_keys()`, `invalidate_pattern()` - Pattern operations
- `_compress_data()`, `_decompress_data()` - Compression
- `_update_memory_cache()`, `_check_memory_cache()` - L1 cache management
- `get_stats()`, `get_memory_usage()` - Basic statistics

#### Methods Overridden for AI-Specific Behavior:
```python
class AIResponseCache(GenericRedisCache):
    
    def _ai_get_success_callback(self, key: str, value: Any, source: str) -> None:
        """AI-specific callback for successful get operations."""
        # AI-specific metrics tracking via composition
        text_tier = self._get_text_tier_from_key(key)
        operation = self._extract_operation_from_key(key)
        
        self._record_ai_cache_hit(source, '', operation or '', text_tier)
        
        if operation:
            self.ai_metrics['cache_hits_by_operation'][operation] += 1
            
        logger.debug(f"AI cache hit: {operation} ({text_tier} tier, {source} cache)")
        
    def _ai_get_miss_callback(self, key: str) -> None:
        """AI-specific callback for cache misses."""
        text_tier = self._get_text_tier_from_key(key)
        operation = self._extract_operation_from_key(key)
        
        if operation:
            self.ai_metrics['cache_misses_by_operation'][operation] += 1
            
        logger.debug(f"AI cache miss: {operation} ({text_tier} tier)")
        
    def _ai_set_success_callback(self, key: str, value: Any, ttl: Optional[int]) -> None:
        """AI-specific callback for successful set operations."""
        operation = self._extract_operation_from_key(key)
        text_tier = self._get_text_tier_from_key(key)
        
        if operation:
            self.ai_metrics['text_tier_distribution'][text_tier] += 1
            
        logger.debug(f"AI cache set: {operation} ({text_tier} tier)")
```

#### AI-Specific Methods (New Implementations):
```python
    async def cache_response(self, text: str, operation: str, 
                            options: Dict[str, Any], response: Dict[str, Any], 
                            question: Optional[str] = None):
        """Cache AI response using inherited Redis operations with AI optimizations."""
        # Generate AI-optimized cache key using extracted key generator
        cache_key = self.key_generator.generate_cache_key(text, operation, options, question)
        
        # Determine text tier for optimization
        text_tier = self._get_text_tier(text)
        
        # Use operation-specific TTL
        ttl = self.operation_ttls.get(operation, self.default_ttl)
        
        # Add AI-specific metadata
        cached_response = {
            **response,
            "cached_at": datetime.now().isoformat(),
            "cache_hit": False,  # This is being cached, not retrieved
            "text_length": len(text),
            "text_tier": text_tier,
            "operation": operation,
            "ai_version": "2.0",  # Track AI cache version
            "key_generation_time": self.key_generator.get_last_generation_time()
        }
        
        # Use inherited set() method from GenericRedisCache
        await self.set(cache_key, cached_response, ttl)
        
        # Update AI-specific metrics
        self._record_cache_operation('set', operation, text_tier)
        self.ai_metrics['text_tier_distribution'][text_tier] += 1
        
        logger.debug(f"Cached AI response for operation '{operation}' with key: {cache_key[:50]}...")
    
    async def get_cached_response(self, text: str, operation: str, 
                                 options: Dict[str, Any], 
                                 question: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached AI response using inherited Redis operations with AI optimizations."""
        cache_key = self.key_generator.generate_cache_key(text, operation, options, question)
        text_tier = self._get_text_tier(text)
        
        # Use inherited get() method from GenericRedisCache
        # This automatically handles L1 memory cache check and Redis fallback
        cached_data = await self.get(cache_key)
        
        if cached_data:
            # Update cache hit metadata
            cached_data["cache_hit"] = True
            cached_data["retrieved_at"] = datetime.now().isoformat()
            
            # Record AI-specific cache hit metrics
            self._record_ai_cache_hit("hybrid", text, operation, text_tier)
            self.ai_metrics['cache_hits_by_operation'][operation] += 1
            
            logger.debug(f"Cache hit for operation '{operation}' with key: {cache_key[:50]}...")
            return cached_data
        
        # Record cache miss
        self._record_ai_cache_miss(text, operation, text_tier)
        self.ai_metrics['cache_misses_by_operation'][operation] += 1
        
        logger.debug(f"Cache miss for operation '{operation}' with key: {cache_key[:50]}...")
        return None
    
    async def invalidate_by_operation(self, operation: str, 
                                    operation_context: str = "") -> int:
        """Invalidate all cache entries for a specific AI operation."""
        pattern = f"ai_cache:op:{operation}*"
        
        # Use inherited invalidate_pattern from GenericRedisCache
        invalidated_count = await self.invalidate_pattern(pattern)
        
        # Record AI-specific invalidation metrics
        if invalidated_count > 0:
            self.performance_monitor.record_invalidation(
                operation_context, invalidated_count, "operation_specific"
            )
            logger.info(f"Invalidated {invalidated_count} entries for operation '{operation}'")
        
        return invalidated_count
```

### 4. Memory Cache Resolution Strategy
**Resolve Memory Cache Handling:**

The AIResponseCache will NOT implement its own memory cache but will rely entirely on the inherited GenericRedisCache memory cache:

```python
# REMOVE from AIResponseCache (handled by parent):
# - self.memory_cache = {}
# - self.memory_cache_size = memory_cache_size  
# - self.memory_cache_order = []
# - def _update_memory_cache()

# AI-specific memory cache optimization:
def _should_promote_to_memory(self, text: str, operation: str) -> bool:
    """Determine if AI response should be promoted to L1 memory cache."""
    text_tier = self._get_text_tier(text)
    
    # Promote small texts and frequently accessed operations
    if text_tier == 'small':
        return True
    
    # Promote stable operations regardless of text size
    if operation in ['sentiment', 'summarize']:
        return True
        
    return False

# Override memory cache promotion in get_cached_response:
async def get_cached_response(self, text: str, operation: str, 
                             options: Dict[str, Any], 
                             question: Optional[str] = None) -> Optional[Dict[str, Any]]:
    # ... existing logic ...
    
    if cached_data and self._should_promote_to_memory(text, operation):
        # Let parent handle memory cache promotion
        # This is already handled by GenericRedisCache.get()
        pass
        
    # ... rest of method ...
```

### 5. Migration Testing Suite
**New file**: `backend/tests/infrastructure/cache/test_ai_cache_migration.py`

**Comprehensive Migration Validation:**
```python
class TestAICacheMigration:
    """Test suite ensuring perfect migration to inheritance model."""
    
    @pytest.fixture
    def original_ai_cache(self):
        """Original AIResponseCache implementation for comparison."""
        # Load original implementation for testing
        pass
    
    @pytest.fixture
    def new_ai_cache(self):
        """New inheritance-based AIResponseCache implementation."""
        return AIResponseCache(
            redis_url="redis://test-redis:6379",
            text_hash_threshold=1000,
            memory_cache_size=50
        )
    
    async def test_identical_behavior_basic_operations(self, original_ai_cache, new_ai_cache):
        """Verify identical behavior for basic operations."""
        test_data = [
            ("Hello world", "summarize", {"max_length": 100}, {"summary": "Hello"}),
            ("Large text" * 1000, "sentiment", {}, {"sentiment": "neutral", "confidence": 0.8}),
        ]
        
        for text, operation, options, response in test_data:
            # Test caching
            await original_ai_cache.cache_response(text, operation, options, response)
            await new_ai_cache.cache_response(text, operation, options, response)
            
            # Test retrieval
            original_result = await original_ai_cache.get_cached_response(text, operation, options)
            new_result = await new_ai_cache.get_cached_response(text, operation, options)
            
            # Compare results (excluding timestamps and version info)
            self._assert_cache_responses_equivalent(original_result, new_result)
    
    async def test_performance_no_regression(self, original_ai_cache, new_ai_cache):
        """Ensure inheritance doesn't introduce performance overhead."""
        benchmark = CachePerformanceBenchmark()
        
        # Benchmark original implementation
        original_results = await benchmark.benchmark_ai_operations(original_ai_cache)
        
        # Benchmark new implementation  
        new_results = await benchmark.benchmark_ai_operations(new_ai_cache)
        
        # Verify no significant performance regression (within 10%)
        for operation in original_results:
            original_time = original_results[operation]['avg_duration_ms']
            new_time = new_results[operation]['avg_duration_ms']
            regression_percentage = (new_time - original_time) / original_time * 100
            
            assert regression_percentage <= 10, f"Performance regression of {regression_percentage}% in {operation}"
    
    async def test_memory_cache_integration_correct(self, new_ai_cache):
        """Validate memory cache works correctly in inheritance model."""
        # Test that small texts are promoted to memory cache
        small_text = "Hello"
        await new_ai_cache.cache_response(small_text, "summarize", {}, {"summary": "Hi"})
        
        # Verify it's in parent's memory cache
        cache_key = new_ai_cache.key_generator.generate_cache_key(small_text, "summarize", {})
        memory_result = new_ai_cache._check_memory_cache(cache_key)
        assert memory_result is not None
        
        # Test that large texts are NOT promoted to memory cache for non-stable operations
        large_text = "Very long text" * 1000
        await new_ai_cache.cache_response(large_text, "questions", {}, {"questions": ["What?"]})
        
        cache_key = new_ai_cache.key_generator.generate_cache_key(large_text, "questions", {})
        memory_result = new_ai_cache._check_memory_cache(cache_key)
        # Should be None or handled appropriately based on implementation
    
    def _assert_cache_responses_equivalent(self, original: Dict[str, Any], new: Dict[str, Any]):
        """Assert that cache responses are functionally equivalent."""
        # Compare essential fields, ignoring timestamps and metadata differences
        essential_fields = ['summary', 'sentiment', 'confidence', 'questions', 'key_points']
        
        for field in essential_fields:
            if field in original:
                assert field in new, f"Missing field {field} in new implementation"
                assert original[field] == new[field], f"Field {field} differs between implementations"
```

### 6. Enhanced AI-Specific Monitoring
**New Methods in AIResponseCache:**

```python
def get_ai_performance_summary(self) -> Dict[str, Any]:
    """Get AI-specific performance metrics and insights."""
    total_operations = sum(self.ai_metrics['cache_hits_by_operation'].values()) + \
                      sum(self.ai_metrics['cache_misses_by_operation'].values())
    
    if total_operations == 0:
        return {"status": "no_operations", "recommendations": []}
    
    hit_rate_by_operation = {}
    for operation in self.operation_ttls.keys():
        hits = self.ai_metrics['cache_hits_by_operation'][operation]
        misses = self.ai_metrics['cache_misses_by_operation'][operation]
        total = hits + misses
        hit_rate_by_operation[operation] = (hits / total * 100) if total > 0 else 0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_ai_operations": total_operations,
        "overall_hit_rate": sum(self.ai_metrics['cache_hits_by_operation'].values()) / total_operations * 100,
        "hit_rate_by_operation": hit_rate_by_operation,
        "text_tier_distribution": dict(self.ai_metrics['text_tier_distribution']),
        "key_generation_stats": self.key_generator.get_key_generation_stats(),
        "optimization_recommendations": self._generate_ai_optimization_recommendations(),
        "inherited_stats": self.get_stats()  # Include parent cache stats
    }

def get_text_tier_statistics(self) -> Dict[str, Any]:
    """Get statistics breakdown by text size tiers."""
    return {
        "tier_configuration": self.text_size_tiers,
        "tier_usage_distribution": dict(self.ai_metrics['text_tier_distribution']),
        "tier_performance_analysis": self._analyze_tier_performance()
    }

def get_operation_performance(self) -> Dict[str, Any]:
    """Get performance breakdown by AI operation type."""
    performance_by_operation = {}
    
    for operation, times in self.ai_metrics['operation_performance'].items():
        if times:
            performance_by_operation[operation] = {
                "avg_duration_ms": sum(times) / len(times),
                "min_duration_ms": min(times),
                "max_duration_ms": max(times),
                "total_operations": len(times),
                "configured_ttl": self.operation_ttls.get(operation, self.default_ttl)
            }
    
    return performance_by_operation

def _record_ai_cache_hit(self, cache_type: str, text: str, operation: str, text_tier: str):
    """Record AI-specific cache hit metrics."""
    self.performance_monitor.record_cache_operation("hit", operation, len(text))
    logger.debug(f"AI cache hit: {operation} ({text_tier} tier, {cache_type} cache)")

def _record_ai_cache_miss(self, text: str, operation: str, text_tier: str):
    """Record AI-specific cache miss metrics."""  
    self.performance_monitor.record_cache_operation("miss", operation, len(text))
    logger.debug(f"AI cache miss: {operation} ({text_tier} tier)")

def _record_operation_performance(self, operation_type: str, duration: float):
    """Record operation performance metrics."""
    self.ai_metrics['operation_performance'][operation_type].append(duration * 1000)  # Convert to ms

def _generate_ai_optimization_recommendations(self) -> List[str]:
    """Generate AI-specific optimization recommendations."""
    recommendations = []
    
    # Analyze hit rates by operation
    for operation, hits in self.ai_metrics['cache_hits_by_operation'].items():
        misses = self.ai_metrics['cache_misses_by_operation'][operation]
        total = hits + misses
        
        if total > 10:  # Only analyze operations with sufficient data
            hit_rate = (hits / total) * 100
            
            if hit_rate < 30:
                recommendations.append(f"Low hit rate for '{operation}' ({hit_rate:.1f}%) - consider increasing TTL")
            elif hit_rate > 90:
                recommendations.append(f"Excellent hit rate for '{operation}' ({hit_rate:.1f}%) - configuration optimal")
    
    # Analyze text tier distribution
    total_requests = sum(self.ai_metrics['text_tier_distribution'].values())
    if total_requests > 0:
        small_percentage = (self.ai_metrics['text_tier_distribution']['small'] / total_requests) * 100
        if small_percentage > 70:
            recommendations.append("High percentage of small texts - consider increasing memory cache size")
        elif small_percentage < 20:
            recommendations.append("Mostly large texts - compression is critical for performance")
    
    return recommendations
```

### 7. Configuration Management (Moved from Phase 3)
**New file**: `backend/app/infrastructure/cache/ai_config.py`

**Rationale**: Creating AIResponseCacheConfig during Phase 2 refactoring simplifies the constructor and enforces validation earlier, making CacheParameterMapper cleaner.

```python
@dataclass
class AIResponseCacheConfig:
    """Complete configuration for AI-specific cache features."""
    
    # AI-specific configuration
    text_hash_threshold: int = 1000
    hash_algorithm: Callable = hashlib.sha256
    
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
    
    # Inherited from GenericRedisCache
    redis_url: str = "redis://redis:6379"
    default_ttl: int = 3600
    compression_threshold: int = 1000
    compression_level: int = 6
    memory_cache_size: int = 100
    redis_auth: Optional[str] = None
    use_tls: bool = False
    
    def to_ai_cache_kwargs(self) -> Dict[str, Any]:
        """Convert config to AIResponseCache constructor kwargs."""
        return asdict(self)
    
    def validate(self) -> ValidationResult:
        """Validate AI cache configuration."""
        errors = []
        
        if self.text_hash_threshold <= 0:
            errors.append("text_hash_threshold must be positive")
            
        if not all(isinstance(v, int) and v > 0 for v in self.text_size_tiers.values()):
            errors.append("text_size_tiers values must be positive integers")
            
        if not all(isinstance(v, int) and v > 0 for v in self.operation_ttls.values()):
            errors.append("operation_ttls values must be positive integers")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

### 8. Integration Testing Framework
**New file**: `backend/tests/infrastructure/cache/test_ai_cache_integration.py`

```python
class TestAICacheIntegration:
    """Integration tests for AIResponseCache with GenericRedisCache inheritance."""
    
    @pytest.fixture
    async def integrated_ai_cache(self):
        """AIResponseCache with full integration."""
        cache = AIResponseCache(
            redis_url="redis://test-redis:6379",
            text_hash_threshold=500,
            memory_cache_size=50,
            compression_threshold=1000
        )
        await cache.connect()
        await cache.clear()  # Start with clean state
        return cache
    
    async def test_end_to_end_ai_workflow(self, integrated_ai_cache):
        """Test complete AI cache workflow with all features."""
        # Test AI response caching and retrieval
        test_scenarios = [
            {
                "text": "Short text for testing",  # Small tier
                "operation": "summarize",
                "options": {"max_length": 50},
                "response": {"summary": "Brief summary", "confidence": 0.9}
            },
            {
                "text": "Medium length text " * 100,  # Medium tier
                "operation": "sentiment", 
                "options": {"model": "gpt-4"},
                "response": {"sentiment": "positive", "confidence": 0.85}
            },
            {
                "text": "Very long text for testing large text handling " * 1000,  # Large tier
                "operation": "key_points",
                "options": {"count": 5},
                "response": {"key_points": ["Point 1", "Point 2"], "confidence": 0.75}
            }
        ]
        
        for scenario in test_scenarios:
            # Cache the response
            await integrated_ai_cache.cache_response(
                scenario["text"], scenario["operation"], 
                scenario["options"], scenario["response"]
            )
            
            # Retrieve and validate
            cached_result = await integrated_ai_cache.get_cached_response(
                scenario["text"], scenario["operation"], scenario["options"]
            )
            
            assert cached_result is not None
            assert cached_result["cache_hit"] == True
            
            # Validate AI-specific metadata
            assert "text_tier" in cached_result
            assert "operation" in cached_result
            assert "ai_version" in cached_result
            
            # Validate response content
            for key, value in scenario["response"].items():
                assert cached_result[key] == value
    
    async def test_inheritance_method_delegation(self, integrated_ai_cache):
        """Test that inherited methods work correctly."""
        # Test basic Redis operations inherited from GenericRedisCache
        await integrated_ai_cache.set("test_key", {"data": "test_value"}, ttl=300)
        
        result = await integrated_ai_cache.get("test_key")
        assert result["data"] == "test_value"
        
        exists = await integrated_ai_cache.exists("test_key")
        assert exists == True
        
        ttl = await integrated_ai_cache.get_ttl("test_key")
        assert 250 <= ttl <= 300  # Allow for small timing differences
        
        await integrated_ai_cache.delete("test_key")
        
        result = await integrated_ai_cache.get("test_key")
        assert result is None
    
    async def test_ai_specific_invalidation(self, integrated_ai_cache):
        """Test AI-specific invalidation operations."""
        # Cache multiple responses for different operations
        operations_data = [
            ("summarize", "Text 1", {"summary": "Summary 1"}),
            ("summarize", "Text 2", {"summary": "Summary 2"}), 
            ("sentiment", "Text 3", {"sentiment": "positive"}),
            ("qa", "Text 4", {"answer": "Answer 1"})
        ]
        
        for operation, text, response in operations_data:
            await integrated_ai_cache.cache_response(text, operation, {}, response)
        
        # Invalidate all 'summarize' operations
        invalidated_count = await integrated_ai_cache.invalidate_by_operation("summarize")
        assert invalidated_count == 2
        
        # Verify 'summarize' operations are gone but others remain
        for operation, text, response in operations_data:
            cached = await integrated_ai_cache.get_cached_response(text, operation, {})
            if operation == "summarize":
                assert cached is None
            else:
                assert cached is not None
    
    async def test_memory_cache_promotion_logic(self, integrated_ai_cache):
        """Test AI-specific memory cache promotion logic."""
        # Small text with stable operation should be promoted
        small_stable_text = "Hello"
        await integrated_ai_cache.cache_response(
            small_stable_text, "summarize", {}, {"summary": "Hi"}
        )
        
        # Retrieve to trigger promotion
        result = await integrated_ai_cache.get_cached_response(small_stable_text, "summarize", {})
        assert result is not None
        
        # Check if it's in memory cache (verify through statistics)
        stats = integrated_ai_cache.get_memory_usage()
        assert stats["memory_cache_entries"] > 0
        
        # Large text with unstable operation should NOT be promoted
        large_unstable_text = "Very long text " * 1000
        await integrated_ai_cache.cache_response(
            large_unstable_text, "qa", {}, {"answer": "Long answer"}
        )
        
        # Should be in Redis but promotion logic should be selective
        result = await integrated_ai_cache.get_cached_response(large_unstable_text, "qa", {})
        assert result is not None
```

### 9. Updated Module Structure
**File Organization:**
```
backend/app/infrastructure/cache/
├── base.py                     # CacheInterface (unchanged)
├── memory.py                   # InMemoryCache (unchanged)  
├── redis_generic.py            # GenericRedisCache (from Phase 1)
├── redis_ai.py                 # AIResponseCache (refactored)
├── key_generator.py            # CacheKeyGenerator (from Phase 1)
├── parameter_mapping.py        # Parameter mapping utilities (new)
├── ai_config.py               # AI-specific configuration (new)
├── security.py                # Security implementation (from Phase 1)
├── migration.py               # Migration utilities (from Phase 1) 
├── monitoring.py              # Enhanced monitoring (updated)
├── benchmarks.py              # Performance benchmarking (from Phase 1)
└── __init__.py                # Updated exports
```

### 10. Enhanced Module Exports
**Update**: `backend/app/infrastructure/cache/__init__.py`

```python
# Base interface
from .base import CacheInterface

# Implementations
from .memory import InMemoryCache
from .redis_generic import GenericRedisCache
from .redis_ai import AIResponseCache  # Updated location

# Components and utilities
from .key_generator import CacheKeyGenerator
from .parameter_mapping import CacheParameterMapper
from .ai_config import AIResponseCacheConfig

# Migration and compatibility (from Phase 1)
from .migration import CacheMigrationManager
from .compatibility import CacheCompatibilityWrapper

# Security (from Phase 1)
from .security import RedisCacheSecurityManager, SecurityConfig

# Monitoring
from .monitoring import (
    CachePerformanceMonitor, PerformanceMetric, 
    CompressionMetric, MemoryUsageMetric, InvalidationMetric
)

# Performance (from Phase 1)
from .benchmarks import CachePerformanceBenchmark, BenchmarkResult

# Updated exports list
__all__ = [
    # Core interfaces and implementations
    "CacheInterface", "InMemoryCache", "GenericRedisCache", "AIResponseCache",
    
    # AI-specific components
    "CacheKeyGenerator", "CacheParameterMapper", "AIResponseCacheConfig",
    
    # Migration and compatibility  
    "CacheMigrationManager", "CacheCompatibilityWrapper",
    
    # Security
    "RedisCacheSecurityManager", "SecurityConfig",
    
    # Monitoring and performance
    "CachePerformanceMonitor", "PerformanceMetric", "CompressionMetric", 
    "MemoryUsageMetric", "InvalidationMetric", "CachePerformanceBenchmark", "BenchmarkResult",
    
    # Redis availability
    "REDIS_AVAILABLE", "aioredis"
]
```

## Enhanced Implementation Timeline

### Week 1: Architecture Analysis and Parameter Mapping
- [ ] Create comprehensive parameter mapping analysis
- [ ] Design inheritance architecture with method override strategy
- [ ] Implement CacheParameterMapper for clean separation
- [ ] Begin AIResponseCache refactoring with proper inheritance

### Week 2: Core Inheritance Implementation
- [ ] Complete AIResponseCache refactoring to inherit from GenericRedisCache
- [ ] Implement proper method overrides vs delegation strategy
- [ ] Resolve memory cache integration (use parent's implementation)
- [ ] Update AI-specific methods to use inherited Redis operations

### Week 3: AI-Specific Features and Monitoring
- [ ] Implement enhanced AI-specific monitoring and analytics
- [ ] Add operation performance tracking and optimization recommendations
- [ ] Create AI-specific configuration management
- [ ] Implement text tier analysis and memory promotion logic

### Week 4: Migration Testing and Validation
- [ ] Comprehensive migration testing suite ensuring identical behavior
- [ ] Performance regression testing with detailed benchmarking
- [ ] Integration testing with GenericRedisCache inheritance
- [ ] Data consistency validation and migration testing

### Week 5: Final Integration and Documentation
- [ ] Update module structure and exports
- [ ] Complete integration with dependency injection system
- [ ] Final performance optimization and validation
- [ ] Documentation updates and preparation for Phase 3

## Enhanced Success Criteria

✅ **Perfect Behavioral Compatibility**: All existing AI cache functionality works identically (validated via comprehensive test suite)  
✅ **Clean Inheritance Architecture**: AIResponseCache properly inherits from GenericRedisCache without code duplication  
✅ **Performance Maintained**: No regression in AI cache operation timing (validated via benchmarking)  
✅ **Memory Cache Integration Resolved**: Single memory cache implementation in parent class used correctly  
✅ **Method Override Clarity**: Clear distinction between inherited methods and AI-specific overrides  
✅ **Parameter Mapping Successful**: Clean separation between AI and generic parameters  
✅ **Enhanced AI Monitoring**: Improved AI-specific analytics and optimization recommendations  
✅ **Migration Validated**: Safe migration from original to inheritance model with data consistency  
✅ **Integration Testing Complete**: Full integration with GenericRedisCache validated  
✅ **Test Coverage Maintained**: >95% coverage for refactored AIResponseCache  

## Enhanced Risk Mitigation

### Architectural Risks
- **Inheritance Complexity**: Comprehensive parameter mapping and method analysis prevents confusion
- **Memory Cache Conflicts**: Clear resolution strategy eliminates duplicate memory cache implementations
- **Performance Overhead**: Detailed benchmarking validates inheritance doesn't introduce overhead

### Migration Risks  
- **Behavioral Changes**: Exhaustive migration testing ensures identical behavior
- **Data Consistency**: Migration tools validate data integrity during transition
- **Integration Failures**: Comprehensive integration testing validates all interaction points

### Development Risks
- **Method Override Confusion**: Clear documentation and analysis of which methods to override vs delegate
- **Configuration Conflicts**: Parameter mapping strategy prevents configuration issues
- **Testing Gaps**: Comprehensive test suite covers all inheritance scenarios and edge cases

## Dependencies for Phase 3

Phase 3 will require:
- ✅ AIResponseCache successfully inheriting from GenericRedisCache
- ✅ All AI functionality preserved and validated
- ✅ Clean parameter separation and configuration management
- ✅ Enhanced AI-specific monitoring and analytics
- ✅ Performance validation showing no regression
- ✅ Complete integration testing validation
- ✅ Migration tools for safe transition

This enhanced plan ensures a robust, maintainable inheritance model that preserves all AI functionality while building cleanly on the GenericRedisCache foundation from Phase 1.