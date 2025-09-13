# **Corrected Refactoring Instructions for Cache Test Suite**

**Goal:** Refactor the specified tests in test_key_generator.py and test_factory.py to remove dependencies on deactivated internal mock fixtures. The new tests will validate the observable behavior of the components by asserting the type and functionality of the real instances they create or interact with.

### **Part 1: Refactoring Tests in backend/tests/infrastructure/cache/key_generator/test_key_generator.py**

**File:** backend/tests/infrastructure/cache/key_generator/test_key_generator.py

**Mock to Replace:** mock_performance_monitor

**Strategy:** The performance_monitor is an optional dependency for the CacheKeyGenerator. The tests should be refactored to remove the mock fixture and instead pass a **real instance** of the CachePerformanceMonitor. The assertion will then focus on the primary functionality of the CacheKeyGenerator itself.

Instructions:  
For each test listed below:

1. Remove the mock_performance_monitor fixture from the function signature.  
2. In the test body, create a real instance of CachePerformanceMonitor.  
3. Pass this real monitor instance into the CacheKeyGenerator constructor.  
4. Assert that the CacheKeyGenerator is functional by calling generate_cache_key and checking the output.

#### **Tests relying on mock_performance_monitor**

* Lines: 91, 944, 1013, 1176, 1264, 1349, 2135 *(Note: Please verify these line numbers correspond to distinct tests, as they seem unusually high for the file's structure. The refactoring pattern below should be applied to each unique test using the mock.)*

**Example Refactor for test_generator_applies_custom_configuration_parameters (line 91):**

* **Before:**
```python  
  def test_generator_applies_custom_configuration_parameters(self, mock_performance_monitor):  
      # ... test logic using the mock ...
```

* **After:**  
```python  
  def test_generator_applies_custom_configuration_parameters(self):  
      """Test that CacheKeyGenerator properly applies custom configuration parameters."""  
      from app.infrastructure.cache.monitoring import CachePerformanceMonitor  
      from app.infrastructure.cache.key_generator import CacheKeyGenerator  
      import hashlib

      # 1. Arrange: Create a real monitor instance.  
      monitor = CachePerformanceMonitor()

      # 2. Act: Pass the real monitor during CacheKeyGenerator instantiation.  
      generator = CacheKeyGenerator(  
          text_hash_threshold=500,  
          hash_algorithm=hashlib.sha256,  
          performance_monitor=monitor  
      )

      # 3. Assert: Verify the generator is configured and functional.  
      assert generator.text_hash_threshold == 500  
      assert generator.performance_monitor is monitor  
      key = generator.generate_cache_key("test", "summarize", {})  
      assert key is not None and "ai_cache:op:summarize" in key
```

### **Part 2: Refactoring Tests in backend/tests/infrastructure/cache/factory/test_factory.py**

**File:** backend/tests/infrastructure/cache/factory/test_factory.py

**Strategy:** Replace tests that check if a mock was *called correctly* with tests that check if the factory *returns a functional, real cache object*.

Instructions:  
For each test listed below:

1. Remove the mock fixture (e.g., mock_generic_redis_cache) from the function signature.  
2. In the test body, create an instance of the real CacheFactory.  
3. await the relevant factory method.  
4. Assert the type of the returned object is the expected real cache class (or a valid fallback like InMemoryCache).  
5. Perform a simple set/get operation to prove the returned cache is functional.

#### **A. Tests relying on mock_ai_response_cache**

* Lines: 600, 649, 1320

**Example Refactor for test_for_ai_app_creates_ai_response_cache_with_default_settings (line 600):**

* **Before:**
```python  
async def test_for_ai_app_creates_ai_response_cache_with_default_settings(self, mock_ai_response_cache):  
```

* **After:**  
```python  
  @pytest.mark.asyncio  
  async def test_for_ai_app_creates_ai_response_cache_with_default_settings(self):  
      """Test that for_ai_app() creates a cache with AI-optimized behavior."""  
      from app.infrastructure.cache.redis_ai import AIResponseCache  
      from app.infrastructure.cache.memory import InMemoryCache  
      from app.infrastructure.cache.factory import CacheFactory

      factory = CacheFactory()  
      cache = await factory.for_ai_app()

      assert isinstance(cache, (AIResponseCache, InMemoryCache)) # It should be AIResponseCache or a memory fallback

      # Prove it's a functional cache  
      await cache.set("test:ai_default", "value")  
      assert await cache.get("test:ai_default") == "value"
```

#### **B. Tests relying on mock_generic_redis_cache**

* Lines: 938, 986, 1085, 1265, 1378

**Example Refactor for test_for_testing_uses_test_database_for_isolation (line 938):**

* **Before:**
```python  
async def test_for_testing_uses_test_database_for_isolation(self, mock_generic_redis_cache):  
```
* **After:**  
```python  
  @pytest.mark.asyncio  
  async def test_for_testing_uses_test_database_for_isolation(self):  
      """Test that for_testing() uses Redis test database for test isolation."""  
      # This test requires a running Redis instance or fakeredis to pass.  
      from app.infrastructure.cache.redis_generic import GenericRedisCache  
      from app.infrastructure.cache.factory import CacheFactory  
      import pytest

      factory = CacheFactory()  
      cache = await factory.for_testing()

      # Skip if fallback occurred, as this test is Redis-specific  
      if not isinstance(cache, GenericRedisCache):  
          pytest.skip("Redis is not available for this test.")

      assert '/15' in cache.redis_url # Default test DB is 15
```

#### **C. Tests relying on mock_memory_cache**

* Lines: 750, 1038, 1184, 1633

**Example Refactor for test_for_web_app_handles_redis_connection_failure_with_memory_fallback (line 750):**

* **Before:**
```python  
async def test_for_web_app_handles_redis_connection_failure_with_memory_fallback(self, mock_memory_cache):  
```
* **After:**  
```python  
  @pytest.mark.asyncio  
  async def test_for_web_app_handles_redis_connection_failure_with_memory_fallback(self):  
      """Test that for_web_app() falls back to InMemoryCache when Redis connection fails."""  
      from app.infrastructure.cache.memory import InMemoryCache  
      from app.infrastructure.cache.factory import CacheFactory

      factory = CacheFactory()

      # Use an impossible Redis URL to force a connection failure  
      cache = await factory.for_web_app(  
          redis_url="redis://nonexistent-host:9999",  
          fail_on_connection_error=False  
      )

      assert isinstance(cache, InMemoryCache)

      # Prove the fallback cache is functional  
      await cache.set("test:fallback", "data")  
      assert await cache.get("test:fallback") == "data"  
```