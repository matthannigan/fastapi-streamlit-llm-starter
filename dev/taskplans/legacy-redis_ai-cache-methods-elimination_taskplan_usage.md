# Usage of `get_cached_response()` and `cache_response()` in Backend Codebase

**Generated:** 2025-08-25  
**Scope:** All files in `backend/` excluding `backend/tests.old/`

## Summary
Found **32 files** containing references to the deprecated cache methods, including:
- **8 production code files** that need updating
- **14 test files** that need updating after production code changes
- **8 contract/type definition files** that need synchronization
- **2 example files** for documentation

## Production Code Files (HIGH PRIORITY)

### 1. `backend/app/services/text_processor.py`
**4 instances** - Core service using deprecated methods
- Line 340: `cached_response = await self.cache_service.get_cached_response(text, operation_value, {}, question)`
- Line 386: `cached_response = await self.cache_service.get_cached_response(`
- Line 406: Comment referencing `cache_response` storage format
- Line 467: `await self.cache_service.cache_response(`

### 2. `backend/app/dependencies.py`
**2 instances** - Dependency injection examples
- Line 483: `cached_result = await cache.get_cached_response(` (in docstring example)
- Line 491: `await cache.cache_response(text, "summarization", {}, result)` (in docstring example)

### 3. `backend/app/infrastructure/cache/dependencies.py`
**2 instances** - Cache dependency providers
- Line 64: `cached_result = await ai_cache.cache_response(` (in docstring)
- Line 519: `result = await ai_cache.cache_response(` (in docstring)

### 4. `backend/app/infrastructure/cache/redis_ai.py`
**7 instances** - The actual method definitions plus internal references
- Line 35: Docstring mentioning the methods
- Line 945: `async def cache_response(` - METHOD DEFINITION
- Line 977: Internal call to `self.set()` within `cache_response()`
- Line 984: Another internal reference
- Line 1079: Return type annotation
- Line 1083: `async def get_cached_response(` - METHOD DEFINITION
- Line 1116: Docstring example using the method

### 5. `backend/app/infrastructure/cache/redis.py`
**5 instances** - Base class with placeholder implementations
- Line 62: Method signature in docstring
- Line 70: Method signature in docstring
- Line 385: `async def get_cached_response(` - base implementation
- Line 528: `def cache_response(` - base implementation
- Line 563: Return statement in method

### 6. `backend/app/infrastructure/cache/compatibility.py`
**16 instances** - Compatibility wrapper (TO BE DELETED)
- Lines 99, 134-135, 170, 186, 191, 195-196, 215, 218, 235, 240, 244-245, 271
- These are all part of the compatibility wrapper implementation

### 7. `backend/app/infrastructure/cache/factory.py`
**1 instance** - Factory pattern reference
- Line 434: Reference in configuration or factory method

### 8. `backend/app/infrastructure/cache/__init__.py`
**2 instances** - Package exports
- Line 71: Export statement
- Line 79: Export statement

### 9. `backend/app/infrastructure/__init__.py`
**1 instance** - Higher-level package export
- Line 97: Export statement

## Contract/Type Definition Files (MEDIUM PRIORITY)

These `.pyi` files need to be updated to match the production code changes:

1. `backend/contracts/dependencies.pyi` - Lines 475, 483
2. `backend/contracts/infrastructure/__init__.pyi` - Line 97
3. `backend/contracts/infrastructure/cache/__init__.pyi` - Lines 71, 79
4. `backend/contracts/infrastructure/cache/compatibility.pyi` - Lines 91, 113, 124
5. `backend/contracts/infrastructure/cache/dependencies.pyi` - Lines 64, 285
6. `backend/contracts/infrastructure/cache/factory.pyi` - Line 229
7. `backend/contracts/infrastructure/cache/redis.pyi` - Lines 62, 70, 186, 202, 230
8. `backend/contracts/infrastructure/cache/redis_ai.pyi` - Lines 35, 163, 188, 197, 224

## Test Files (LOW PRIORITY - Update After Production)

### Current Tests (need updating)
1. `backend/tests/services/test_text_processing.py` - 18 instances
2. `backend/tests/api/v1/test_text_processing_endpoints.py` - 8 instances
3. `backend/tests/integration/test_request_isolation.py` - 8 instances
4. `backend/tests/core/test_dependencies.py` - 2 instances
5. `backend/tests/conftest.py` - 2 instances
6. `backend/tests/unit/infrastructure/cache/redis_ai/test_redis_ai_core_operations.py` - 51 instances
7. `backend/tests/unit/infrastructure/cache/redis_ai/test_redis_ai_error_handling.py` - 10 instances
8. `backend/tests/unit/infrastructure/cache/redis_ai/test_redis_ai_connection.py` - 3 instances
9. `backend/tests/unit/infrastructure/cache/redis_ai/test_redis_ai_inheritance.py` - 2 instances
10. `backend/tests/unit/infrastructure/cache/redis_ai/test_redis_ai_invalidation.py` - 1 instance
11. `backend/tests/unit/infrastructure/cache/redis_ai/test_redis_ai_statistics.py` - 2 instances
12. `backend/tests/unit/infrastructure/cache/redis_ai/__init__.py` - 1 instance
13. `backend/tests/unit/infrastructure/cache/factory/conftest.py` - 4 instances

## Example/Documentation Files (UPDATE LAST)

1. `backend/examples/advanced_infrastructure_demo.py` - Lines 166, 178
2. `backend/examples/cache_configuration_examples.py` - Lines 91, 101, 185, 189, 419, 443, 486, 489, 551, 555

## README Files

1. `backend/app/infrastructure/cache/README.md` - Lines 473, 481, 564, 575 (documentation references)

## Refactoring Strategy

### Phase 1: Update Core Implementation
1. Modify `redis_ai.py` to remove `get_cached_response()` and `cache_response()` methods
2. Enhance the inherited `get()` and `set()` methods with AI-specific logic if needed
3. Update `redis.py` base class to remove placeholder methods

### Phase 2: Update Service Layer
1. Update `text_processor.py` to use `get()` and `set()` methods
2. Update method signatures to match new interface

### Phase 3: Update Dependencies and Exports
1. Remove exports from `__init__.py` files
2. Update dependency injection examples in `dependencies.py`
3. Delete `compatibility.py` entirely

### Phase 4: Update Contracts
1. Synchronize all `.pyi` files with implementation changes

### Phase 5: Update Tests
1. Update all test files to use new method names
2. Ensure tests still pass with new interface

### Phase 6: Update Documentation
1. Update example files
2. Update README documentation
3. Update docstring examples

## Migration Pattern

Replace old calls with new pattern:

**OLD:**
```python
# Getting cached response
cached = await cache.get_cached_response(text, operation, options, question)

# Setting cached response
await cache.cache_response(text, operation, options, response, question)
```

**NEW:**
```python
# Getting cached response
key = cache.key_generator.generate_cache_key(text, operation, options, question)
cached = await cache.get(key)

# Setting cached response
key = cache.key_generator.generate_cache_key(text, operation, options, question)
await cache.set(key, response, ttl=ttl)
```

Or if the key generation should be internal to the cache:

**NEW (Alternative):**
```python
# Create a structured request object
cache_request = {
    'text': text,
    'operation': operation,
    'options': options,
    'question': question
}

# Get/Set with structured request
cached = await cache.get_ai_response(cache_request)
await cache.set_ai_response(cache_request, response, ttl=ttl)
```
