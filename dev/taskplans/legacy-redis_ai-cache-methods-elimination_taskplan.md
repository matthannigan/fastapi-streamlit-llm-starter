# Legacy Redis AI Cache Methods Elimination - Taskplan

**PRD Reference:** `dev/taskplans/pending/legacy-redis_ai-cache-methods-elimination_taskplan_PRD.md`  
**Status:** 🟡 **PENDING**  
**Estimated Effort:** 8-10 hours  
**Primary Focus:** Complete elimination of domain-specific methods from infrastructure layer and proper architectural separation  

## Overview
This taskplan implements the complete elimination of legacy cache methods (`cache_response()` and `get_cached_response()`) from the AIResponseCache infrastructure service, moving all domain-specific logic to the TextProcessorService. This ensures proper infrastructure/domain separation and enforces use of the standard cache interface.

## Deliverables Summary

### 🔧 **Deliverable 1: Domain Layer Cache Logic Migration** - ⏳ PENDING
**Scope:** Move domain-specific cache logic from infrastructure to domain layer  
**Effort:** 3-4 hours  
**Dependencies:** Legacy code review completed  

### 🧹 **Deliverable 2: Infrastructure Layer Cleanup** - ⏳ PENDING
**Scope:** Remove legacy methods and domain knowledge from infrastructure  
**Effort:** 2-3 hours  
**Dependencies:** Deliverable 1 completed  

### 🧪 **Deliverable 3: Integration and Validation** - ⏳ PENDING
**Scope:** Comprehensive testing of refactored architecture  
**Effort:** 2 hours  
**Dependencies:** Deliverable 2 completed  

### 📚 **Deliverable 4: Documentation and Examples** - ⏳ PENDING
**Scope:** Update all documentation to reflect proper architectural patterns  
**Effort:** 1-2 hours  
**Dependencies:** Deliverable 3 completed  

---

## Deliverable 1: Domain Layer Cache Logic Migration

### Tasks Overview
**Goal:** Implement domain-specific cache logic in TextProcessorService and update all cache operations to use standard interface.

### Task List

#### 🔧 **Task 1.1: Create Domain Cache Key Building Logic**
**Status:** ⏳ PENDING  
**Effort:** 90 minutes  
**Files:**
- `backend/app/services/text_processor.py`

**Actions:**
- [ ] Create `_build_cache_key()` method in TextProcessorService
- [ ] Implement question parameter handling through options dictionary
- [ ] Add domain-specific cache key logic (text tier analysis, operation-specific patterns)
- [ ] Create `_get_ttl_for_operation()` method for operation-specific TTL logic
- [ ] Add comprehensive error handling and validation

**Implementation Example:**
```python
class TextProcessorService:
    async def _build_cache_key(self, text: str, operation: str, options: Dict[str, Any], question: Optional[str] = None) -> str:
        # Embed question in options if present
        if question:
            options = {**options, 'question': question}
        
        # Use generic cache key building
        return self.cache_service.build_key(text, operation, options)
    
    def _get_ttl_for_operation(self, operation: str) -> Optional[int]:
        # Operation-specific TTL logic
        operation_ttls = {
            'summarize': 7200,  # 2 hours
            'sentiment': 3600,  # 1 hour
            'qa': 1800,         # 30 minutes
        }
        return operation_ttls.get(operation)
```

**Validation:**
- [ ] Method correctly handles all operation types
- [ ] Question parameter properly embedded in options
- [ ] Error handling matches current patterns
- [ ] TTL logic maintains current behavior

#### 🔄 **Task 1.2: Update Cache Operations to Use Standard Interface**
**Status:** ⏳ PENDING  
**Effort:** 120 minutes  
**Files:**
- `backend/app/services/text_processor.py`

**Actions:**
- [ ] Replace all `get_cached_response()` calls with `cache.get(key)`
- [ ] Replace all `cache_response()` calls with `cache.set(key, value, ttl)`
- [ ] Update fallback response method cache operations
- [ ] Update process_text_request cache operations  
- [ ] Update all Q&A operation cache handling
- [ ] Ensure consistent error handling patterns

**Current Legacy Patterns to Replace:**
```python
# Replace these patterns:
cached_response = await self.cache_service.get_cached_response(text, operation_value, {}, question)
await self.cache_service.cache_response(text, operation_value, options, response, question)

# With these patterns:
cache_key = await self._build_cache_key(text, operation_value, options, question)
cached_response = await self.cache_service.get(cache_key)
await self.cache_service.set(cache_key, response, self._get_ttl_for_operation(operation_value))
```

**Validation:**
- [ ] All legacy method calls replaced
- [ ] Standard cache interface used throughout
- [ ] Cache key generation consistent
- [ ] TTL handling preserved

#### 🧪 **Task 1.3: Add Domain Service Cache Tests**
**Status:** ⏳ PENDING  
**Effort:** 60 minutes  
**Files:**
- `backend/tests/services/test_text_processor.py`

**Actions:**
- [ ] Add tests for `_build_cache_key()` method
- [ ] Add tests for `_get_ttl_for_operation()` method
- [ ] Update existing cache-related tests to use standard interface mocking
- [ ] Add integration tests for cache operations across all operation types
- [ ] Add tests for question parameter handling in options

**Test Categories:**
- [ ] **Cache Key Building:** Validate key generation logic
- [ ] **Question Handling:** Ensure question properly embedded in options
- [ ] **TTL Logic:** Verify operation-specific TTL assignment
- [ ] **Standard Interface Usage:** Confirm `get()`/`set()` usage patterns
- [ ] **Error Scenarios:** Test cache failure handling

**Validation:**
- [ ] All new domain logic properly tested
- [ ] Test mocks use standard cache interface
- [ ] Edge cases and error conditions covered
- [ ] Test coverage maintained >70% for domain services

---

## Deliverable 2: Infrastructure Layer Cleanup

### Tasks Overview
**Goal:** Remove all domain-specific methods and knowledge from AIResponseCache, maintaining only generic cache operations.

### Task List

#### 🗑️ **Task 2.1: Remove Legacy Methods from AIResponseCache**
**Status:** ⏳ PENDING  
**Effort:** 45 minutes  
**Files:**
- `backend/app/infrastructure/cache/redis_ai.py`

**Actions:**
- [ ] Remove `cache_response()` method entirely (lines ~945-1076)
- [ ] Remove `get_cached_response()` method entirely (lines ~1084-1200+)
- [ ] Remove all related helper methods and domain-specific logic
- [ ] Clean up imports and dependencies related to removed methods
- [ ] Update class docstring to reflect standard interface usage

**Methods to Remove:**
```python
# Remove these methods completely:
def cache_response(self, text: str, operation: str, options: Dict[str, Any], response: Dict[str, Any], question: Optional[str] = None)
async def get_cached_response(self, text: str, operation: str, options: Optional[Dict[str, Any]] = None, question: Optional[str] = None)
```

**Validation:**
- [ ] Legacy methods completely removed
- [ ] No remaining domain-specific logic in infrastructure
- [ ] Class maintains standard cache interface only
- [ ] All performance monitoring preserved

#### 🔧 **Task 2.2: Add Generic Cache Key Helper Method**
**Status:** ⏳ PENDING  
**Effort:** 30 minutes  
**Files:**
- `backend/app/infrastructure/cache/redis_ai.py`

**Actions:**
- [ ] Add optional `build_key()` helper method for generic key generation
- [ ] Ensure method has no domain-specific knowledge
- [ ] Delegate to CacheKeyGenerator for actual key generation
- [ ] Add comprehensive documentation for generic usage

**Implementation Example:**
```python
def build_key(self, text: str, operation: str, options: Dict[str, Any]) -> str:
    """
    Build cache key using generic key generation logic.
    
    Args:
        text: Input text for key generation
        operation: Operation type (generic string)
        options: Options dictionary containing all operation-specific data
        
    Returns:
        Generated cache key string
    """
    return self.key_generator.generate_cache_key(text, operation, options)
```

**Validation:**
- [ ] Method is completely generic (no domain knowledge)
- [ ] Delegates properly to CacheKeyGenerator
- [ ] Documentation reflects generic usage
- [ ] Integration with domain services works correctly

#### 🔄 **Task 2.3: Update CacheKeyGenerator to Remove Domain Parameters**
**Status:** ⏳ PENDING  
**Effort:** 45 minutes  
**Files:**
- `backend/app/infrastructure/cache/key_generator.py`

**Actions:**
- [ ] Remove `question` parameter from `generate_cache_key()` method signature
- [ ] Update method to extract question from options dictionary
- [ ] Ensure backwards compatibility for key generation (same keys produced)
- [ ] Update method documentation to reflect generic approach
- [ ] Add validation for options dictionary format

**Current Signature to Update:**
```python
# Change from:
def generate_cache_key(self, text: str, operation: str, options: Dict[str, Any], question: Optional[str] = None) -> str:

# To:
def generate_cache_key(self, text: str, operation: str, options: Dict[str, Any]) -> str:
    question = options.get('question')  # Extract from options
    # Rest of logic remains the same
```

**Validation:**
- [ ] Method signature updated correctly
- [ ] Question extraction from options works
- [ ] Generated keys remain identical (backwards compatibility)
- [ ] All edge cases handled properly

#### 🧪 **Task 2.4: Update Infrastructure Tests**
**Status:** ⏳ PENDING  
**Effort:** 60 minutes  
**Files:**
- `backend/tests/infrastructure/cache/test_redis_ai.py`
- `backend/tests/infrastructure/cache/test_key_generator.py`

**Actions:**
- [ ] Remove all tests for legacy methods (`cache_response`, `get_cached_response`)
- [ ] Add tests for new `build_key()` helper method
- [ ] Update CacheKeyGenerator tests to use options dictionary for question
- [ ] Ensure all tests use standard cache interface (`get`, `set`, `delete`)
- [ ] Add tests validating zero domain knowledge in infrastructure

**Test Updates:**
- [ ] **Remove Legacy Tests:** Delete tests for removed methods
- [ ] **Standard Interface Tests:** Ensure all tests use `get()`/`set()` patterns
- [ ] **Generic Key Building:** Test `build_key()` helper method
- [ ] **Options Dictionary:** Test question handling through options
- [ ] **Architecture Validation:** Ensure infrastructure has zero domain knowledge

**Validation:**
- [ ] All legacy method tests removed
- [ ] Infrastructure tests maintain >90% coverage
- [ ] Tests validate architectural separation
- [ ] Performance tests continue to pass

---

## Deliverable 3: Integration and Validation

### Tasks Overview
**Goal:** Comprehensive testing and validation of the refactored architecture to ensure functionality, performance, and proper separation.

### Task List

#### 🔗 **Task 3.1: End-to-End Integration Testing**
**Status:** ⏳ PENDING  
**Effort:** 60 minutes  
**Focus:** Complete system functionality with new architecture

**Test Categories:**
- [ ] **API Endpoint Integration:** All text processing endpoints use new cache patterns
- [ ] **Service Integration:** TextProcessorService integrates properly with refactored cache
- [ ] **Question Handling:** Q&A operations work correctly with options-based question handling
- [ ] **Error Scenarios:** System handles cache failures gracefully
- [ ] **Performance Integration:** Monitoring and metrics collection continues working

**Commands:**
```bash
# Run comprehensive integration tests
make test-backend-integration

# Run service-specific integration tests
../.venv/bin/python -m pytest tests/integration/ -v -k "text_processor"

# Run API endpoint tests
../.venv/bin/python -m pytest tests/api/ -v -k "cache"
```

**Validation:**
- [ ] All API endpoints function correctly
- [ ] Cache integration works across all services
- [ ] Q&A operations handle questions properly
- [ ] Error handling maintains expected behavior
- [ ] Performance monitoring remains functional

#### ⚡ **Task 3.2: Cache Key Consistency Validation**
**Status:** ⏳ PENDING  
**Effort:** 30 minutes  
**Focus:** Ensure cache keys remain identical before/after refactoring

**Validation Areas:**
- [ ] **Key Generation Logic:** Same inputs produce identical keys
- [ ] **Question Handling:** Questions in options produce same keys as legacy parameter
- [ ] **Edge Cases:** Empty options, missing questions, special characters handled consistently
- [ ] **Performance:** Key generation performance unchanged

**Test Approach:**
```python
# Create test cases comparing legacy vs new key generation
def test_cache_key_consistency():
    # Legacy approach (reference implementation)
    legacy_key = old_key_generator.generate_cache_key(text, operation, options, question)
    
    # New approach (options-based)
    new_options = {**options, 'question': question} if question else options
    new_key = new_key_generator.generate_cache_key(text, operation, new_options)
    
    assert legacy_key == new_key
```

**Validation:**
- [ ] All cache keys remain identical
- [ ] Question handling produces correct keys
- [ ] Performance characteristics unchanged
- [ ] No cache misses from key generation changes

#### 🏗️ **Task 3.3: Architecture Separation Validation**
**Status:** ⏳ PENDING  
**Effort:** 30 minutes  
**Focus:** Confirm proper infrastructure/domain separation achieved

**Architecture Validation:**
- [ ] **Infrastructure Layer:** AIResponseCache contains zero domain knowledge
- [ ] **Domain Layer:** TextProcessorService owns all business-specific cache logic  
- [ ] **Interface Compliance:** Only standard cache interface used throughout
- [ ] **Dependency Direction:** Domain layer depends on infrastructure, not vice versa

**Validation Commands:**
```bash
# Search for any remaining domain violations in infrastructure
grep -r "question" backend/app/infrastructure/cache/ --exclude="*.pyc"
grep -r "text_processor\|domain" backend/app/infrastructure/cache/ --exclude="*.pyc"

# Verify standard interface usage
grep -r "cache_response\|get_cached_response" backend/app/ --exclude-dir="tests.old"
```

**Validation:**
- [ ] No domain-specific references in infrastructure layer
- [ ] All cache operations use standard interface
- [ ] Clean architectural boundaries maintained
- [ ] Dependency direction properly enforced

---

## Deliverable 4: Documentation and Examples

### Tasks Overview
**Goal:** Update all documentation, examples, and architectural guidance to reflect proper infrastructure/domain separation patterns.

### Task List

#### 📖 **Task 4.1: Update Cache Architecture Documentation**
**Status:** ⏳ PENDING  
**Effort:** 45 minutes  
**Files:**
- `CLAUDE.md`
- `README.md`
- `backend/app/infrastructure/cache/README.md`

**Actions:**
- [ ] Update architecture documentation to show proper separation
- [ ] Remove references to legacy methods from all documentation
- [ ] Add examples of proper domain service cache usage
- [ ] Update cache interface documentation to emphasize standard patterns
- [ ] Add architectural guidance on infrastructure/domain separation

**Documentation Updates:**
- [ ] **CLAUDE.md:** Update cache usage examples in developer guidelines
- [ ] **README.md:** Update cache examples to show standard interface usage
- [ ] **Cache README.md:** Add architectural separation guidance
- [ ] **Docstrings:** Update all method docstrings to reflect current patterns

**Validation:**
- [ ] No references to legacy methods remain
- [ ] Examples demonstrate proper architectural patterns
- [ ] Developer guidance is clear and accurate
- [ ] Architecture principles are well documented

#### 💡 **Task 4.2: Update Usage Examples and Code Samples**
**Status:** ⏳ PENDING  
**Effort:** 30 minutes  
**Files:**
- `backend/examples/cache/`
- Documentation in various files

**Actions:**
- [ ] Update all cache usage examples to use standard interface
- [ ] Remove examples of legacy method usage
- [ ] Add examples of domain-specific cache key building
- [ ] Update API endpoint examples to show proper cache integration
- [ ] Add examples of question handling through options dictionary

**Example Updates:**
```python
# Update examples from:
cached_response = await cache.get_cached_response(text, "summarize", {"max_length": 100})

# To:
cache_key = await service._build_cache_key(text, "summarize", {"max_length": 100})
cached_response = await cache.get(cache_key)
```

**Validation:**
- [ ] All examples use current architectural patterns
- [ ] Code samples are accurate and functional
- [ ] Examples demonstrate best practices
- [ ] Documentation consistency maintained

#### 🎯 **Task 4.3: Address Legacy Code Review Items**
**Status:** ⏳ PENDING  
**Effort:** 15 minutes  
**Files:**
- Files identified in `dev/code-reviews/2025-08-25/cache-legacy-review_claude2.md`

**Actions:**
- [ ] Update documentation examples that still use legacy methods
- [ ] Remove deprecated method references from docstrings
- [ ] Clean up any remaining legacy patterns in examples
- [ ] Validate that legacy review items are fully addressed

**Validation:**
- [ ] All legacy review items addressed
- [ ] No legacy patterns remain in examples
- [ ] Documentation reflects current architecture
- [ ] Code review concerns resolved

---

## Success Criteria Validation

### ✅ Primary Success Criteria
- [ ] **Complete Method Elimination:** `cache_response()` and `get_cached_response()` methods completely removed
- [ ] **Standard Interface Enforcement:** All cache operations use `get()`, `set()`, `delete()` methods only
- [ ] **Domain Logic Migration:** All business-specific cache logic moved to TextProcessorService
- [ ] **Architecture Separation:** Infrastructure layer contains zero domain knowledge
- [ ] **Functionality Preserved:** All existing functionality works identically

### ✅ Secondary Success Criteria  
- [ ] **Performance Maintained:** Cache performance and behavior unchanged
- [ ] **Test Coverage:** Infrastructure >90%, Domain >70% test coverage maintained
- [ ] **Documentation Updated:** All documentation reflects new architectural patterns
- [ ] **Cache Key Consistency:** Generated cache keys remain identical (backwards compatibility)
- [ ] **Error Handling:** Consistent error handling patterns maintained

## Logical Dependency Chain

### Foundation Phase (Complete First)
1. **Task 1.1** - Create domain cache key building logic
2. **Task 1.2** - Update all cache operations to standard interface
3. **Task 1.3** - Add comprehensive domain service tests

### Infrastructure Cleanup (After Domain Migration)
4. **Task 2.1** - Remove legacy methods from AIResponseCache
5. **Task 2.2** - Add generic cache key helper
6. **Task 2.3** - Update CacheKeyGenerator to remove domain parameters
7. **Task 2.4** - Update infrastructure tests

### Validation Phase (After Cleanup)
8. **Task 3.1** - End-to-end integration testing
9. **Task 3.2** - Cache key consistency validation
10. **Task 3.3** - Architecture separation validation

### Documentation Phase (Final)
11. **Task 4.1** - Update architecture documentation
12. **Task 4.2** - Update usage examples
13. **Task 4.3** - Address legacy code review items

## Risk Mitigation

### Technical Risks
- **Cache Key Changes:** Comprehensive validation ensures keys remain identical
- **Performance Regression:** Before/after benchmarking validates performance maintained
- **Integration Failures:** Incremental testing at each phase catches issues early

### Development Risks
- **Incomplete Migration:** Comprehensive grep searches validate no legacy patterns remain
- **Test Coverage Gaps:** Systematic test updates maintain required coverage levels
- **Documentation Drift:** Validation tasks ensure documentation stays current

**Final Status:** Ready for implementation following the complete elimination approach outlined in the PRD.