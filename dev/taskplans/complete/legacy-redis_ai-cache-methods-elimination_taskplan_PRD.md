# Legacy `redis_ai` Cache Methods Elimination PRD

## Overview  
The AIResponseCache infrastructure service currently contains legacy domain-specific methods that violate core architectural principles of infrastructure/domain separation. The `cache_response()` and `get_cached_response()` methods are convenience wrappers that bypass the standard cache interface (`get()`, `set()`, `delete()`) and embed domain-specific knowledge (Q&A `question` parameter) directly into the infrastructure layer. This refactoring will **completely eliminate** these methods and enforce proper use of the standard cache interface, moving all domain-specific logic to the appropriate domain services.

## Core Features  
**Complete Method Elimination:**
- Remove `cache_response()` and `get_cached_response()` methods entirely from AIResponseCache
- Enforce exclusive use of standard cache interface: `get()`, `set()`, `delete()` inherited from GenericRedisCache
- Eliminate architectural violations that bypass proper cache abstraction

**Domain Logic Migration:**
- Move cache key generation logic from infrastructure to domain layer (TextProcessorService)
- Migrate `question` parameter handling to domain layer through `options` dictionary
- Create domain-specific cache key building methods in TextProcessorService
- Ensure infrastructure service contains zero domain-specific knowledge

**Infrastructure Simplification:**
- Maintain only generic cache operations in AIResponseCache
- Remove domain-specific parameters from CacheKeyGenerator
- Add optional generic helper method `build_key()` for consistent key generation patterns
- Preserve all performance monitoring, compression, and Redis-specific optimizations

## User Experience  
**Developer Personas:**
- Infrastructure developers maintaining cache services
- Domain service developers (text processing, future AI services)
- API consumers using cached AI responses

**Key User Flows:**
- **Cache Storage Flow**: Domain service builds cache key using domain logic, then calls standard `cache.set(key, response, ttl)`
- **Cache Retrieval Flow**: Domain service builds cache key using domain logic, then calls standard `cache.get(key)`
- **Migration Flow**: Existing code updated to use proper infrastructure/domain separation patterns

**API Experience Improvements:**
- Enforces proper use of standard cache interface (`get`, `set`, `delete`)
- Domain services take full responsibility for cache key generation and business logic
- Infrastructure layer maintains zero business domain knowledge
- Clear architectural boundaries prevent future domain coupling violations

## Technical Architecture  
**Current State:**
```python
# Infrastructure layer with domain violations
class AIResponseCache(GenericRedisCache):
    def cache_response(text, operation, options, response, question=None)  # Domain-specific method
    async def get_cached_response(text, operation, options=None, question=None)  # Domain-specific method

# Domain layer incorrectly delegating to infrastructure
class TextProcessorService:
    await self.cache_service.get_cached_response(text, operation, {}, question)
```

**Target State:**
```python
# Clean infrastructure layer - no domain knowledge
class AIResponseCache(GenericRedisCache):
    # Only standard cache interface: get(), set(), delete() from parent
    def build_key(self, text: str, operation: str, options: Dict[str, Any]) -> str  # Generic helper

# Domain layer owns all business logic
class TextProcessorService:
    async def _build_cache_key(self, text, operation, options, question=None) -> str:
        if question:
            options = {**options, 'question': question}
        return self.cache_service.build_key(text, operation, options)
    
    cache_key = await self._build_cache_key(text, operation, options, question)
    cached_response = await self.cache_service.get(cache_key)
```

**Component Changes:**
- **AIResponseCache class**: Complete removal of domain-specific methods, keep only standard interface
- **CacheKeyGenerator**: Remove domain-specific `question` parameter, handle via options dictionary
- **TextProcessorService**: Add domain-specific cache key building methods and logic
- **Test suites**: Update all tests to use standard cache interface patterns
- **API endpoints**: Update internal cache management endpoints to use standard interface

**Data Model Changes:**
- No changes to cached data structure or Redis storage patterns
- Question data embedded in options dictionary before key generation
- Cache key generation becomes generic infrastructure utility
- All domain-specific logic moves to appropriate domain services

## Development Roadmap  
**Deliverable 1: Domain Layer Cache Logic Migration**
- Create `_build_cache_key()` method in TextProcessorService with domain-specific logic
- Implement question embedding in options dictionary before key generation
- Update all cache operations in text_processor.py to use standard `get()`/`set()` interface
- Add domain service tests validating new cache key building logic
- Verify end-to-end functionality with standard cache interface

**Deliverable 2: Infrastructure Layer Cleanup**
- Remove `cache_response()` and `get_cached_response()` methods completely from AIResponseCache
- Update CacheKeyGenerator to remove `question` parameter (handle via options)
- Add optional `build_key()` helper method in AIResponseCache for consistency
- Update all infrastructure-level tests to use standard cache interface
- Remove all domain-specific knowledge from infrastructure layer

**Deliverable 3: Integration and Validation**
- Run comprehensive integration tests across all services
- Validate cache performance and functionality unchanged
- Verify proper infrastructure/domain separation maintained
- Test cache key generation consistency before/after refactoring
- Validate Redis operations and data structures unchanged

**Deliverable 4: Documentation and Examples**
- Update all method documentation and examples to show standard interface usage
- Update CLAUDE.md and architectural documentation with proper patterns
- Create architectural guidance on infrastructure/domain separation
- Update example code in README and documentation files

## Logical Dependency Chain
**Foundation (Must Complete First):**
1. **Domain Layer Cache Logic** - Implement cache key building in TextProcessorService first
2. **Standard Interface Usage** - Update all domain service cache operations to use `get()`/`set()`
3. **Integration Testing** - Verify functionality works with standard interface before infrastructure changes

**Infrastructure Cleanup:**
1. **Method Removal** - Safe to remove legacy methods after domain layer is updated
2. **CacheKeyGenerator Cleanup** - Remove domain-specific parameters after usage patterns updated
3. **Infrastructure Tests** - Validate infrastructure layer contains zero domain knowledge

**Validation and Documentation:**
1. **End-to-End Testing** - Verify complete system functionality with new architecture
2. **Performance Validation** - Ensure cache performance unchanged despite architectural improvements
3. **Architectural Review** - Confirm proper infrastructure/domain separation achieved
4. **Documentation Updates** - Reflect new architectural patterns and usage guidelines

## Risks and Mitigations  
**Architectural Transition Risks:**
- **Domain Logic Migration**: Risk of missing business logic during migration - mitigate with comprehensive testing of all Q&A and caching scenarios
- **Cache Key Consistency**: Risk of cache misses if key generation changes - mitigate with thorough key generation validation and backwards compatibility testing
- **Interface Contract Changes**: Risk of breaking existing patterns - mitigate with incremental migration starting with domain layer

**Integration Risks:**
- **Cross-Service Dependencies**: Risk of missing cache dependencies in other services - mitigate with comprehensive codebase search and integration tests
- **Performance Regressions**: Risk of performance impact from architectural changes - mitigate with performance benchmarking before/after
- **Redis Operations**: Risk of changing cached data patterns - mitigate with Redis data structure validation

**Development Risks:**
- **Incomplete Separation**: Risk of leaving domain logic in infrastructure - mitigate with architectural review and comprehensive testing
- **Test Coverage Gaps**: Risk of insufficient test coverage for new patterns - mitigate with comprehensive test scenarios across all operation types
- **Documentation Gaps**: Risk of unclear migration guidance - mitigate with clear architectural documentation and examples

**Migration Strategy:**
- No backwards compatibility layer needed - complete architectural refactoring
- All changes contained within existing service boundaries
- Infrastructure and domain layers clearly separated after migration
- Performance and functionality maintained throughout transition

## Appendix  
**Code References:**
- **Primary Infrastructure**: `backend/app/infrastructure/cache/redis_ai.py`
- **Key Infrastructure Classes**: `AIResponseCache`, `CacheKeyGenerator`
- **Primary Domain Service**: `backend/app/services/text_processor.py`
- **Test Coverage**: `backend/tests/infrastructure/cache/` and `backend/tests/services/`
- **Legacy Review Reference**: `dev/code-reviews/2025-08-25/cache-legacy-review_claude2.md`

**Architectural Principles:**
- **Infrastructure vs Domain Separation**: Infrastructure services must contain zero business domain knowledge
- **Standard Interface Enforcement**: All cache operations must use standard `get()`, `set()`, `delete()` methods
- **Domain Logic Ownership**: Domain services own all business-specific cache logic including key generation
- **Single Responsibility**: Infrastructure provides caching capabilities, domain services provide business logic

**Performance Considerations:**
- Cache key generation performance must remain unchanged
- Redis operations and data structures must remain identical
- Cache hit/miss rates should be unaffected by architectural improvements
- Memory usage patterns should remain consistent
- All performance monitoring and metrics collection preserved

**Success Criteria:**
- AIResponseCache contains zero domain-specific methods or knowledge
- TextProcessorService handles all domain-specific cache logic
- All cache operations use standard interface (`get`, `set`, `delete`)
- Cache performance and functionality identical to current implementation
- Clear architectural separation between infrastructure and domain layers
- Comprehensive test coverage for new architectural patterns