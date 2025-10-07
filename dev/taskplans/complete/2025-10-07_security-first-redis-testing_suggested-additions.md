Based on the new security-first architecture and your project's testing philosophy, here is a comprehensive guide on the new unit and integration tests you should add to your suite.

### New Unit Tests to Add

Your unit testing philosophy emphasizes verifying the documented contract of a single component in complete isolation. The new contracts introduce several new, self-contained components with clear behaviors that are perfect candidates for unit testing.

---
#### 🧪 **1. Test Suite for `app.core.startup.redis_security.RedisSecurityValidator`**

This new component is critical for enforcing the "Fail-Fast Design" goal of your PRD. Its unit tests should verify its validation logic in isolation by mocking the environment detection it depends on.

* **Behavior Under Test**: The `validate_production_security` method's core logic, which should raise a `ConfigurationError` in a production environment with an insecure Redis URL but pass in a development environment.
* **Isolation Strategy**: Mock the `get_environment_info` function to deterministically simulate `production` and `development` environments. This tests the validator's reaction to the environment, not the detection logic itself, adhering to your "mock only at system boundaries" rule.

**Recommended Test Cases for `TestRedisSecurityValidator`:**

* `test_raises_error_for_insecure_url_in_production()`: Mocks a **production** environment and asserts that a `ConfigurationError` is raised when the `redis_url` is `redis://`.
* `test_allows_insecure_url_in_development()`: Mocks a **development** environment and asserts that no error is raised for a `redis://` URL.
* `test_allows_secure_url_in_production()`: Mocks a **production** environment and asserts that no error is raised for a `rediss://` URL.
* `test_respects_insecure_override_in_production()`: Mocks a **production** environment, sets `insecure_override=True`, and asserts that no error is raised for a `redis://` URL.

---
#### 🔬 **2. Test Suite for `app.core.environment.EnvironmentDetector`**

This new component has a clear public contract for detecting the environment based on external state (environment variables). Unit tests should validate this detection logic by manipulating `os.environ` using `pytest`'s `monkeypatch` fixture.

* **Behavior Under Test**: The `detect_environment` method should correctly identify the environment and assign a confidence score based on various environment variables, as described in its docstring.
* **Isolation Strategy**: Use `monkeypatch` to set and unset environment variables (`ENVIRONMENT`, `NODE_ENV`, etc.) to test the detector's logic without affecting the actual test runner's environment.

**Recommended Test Cases for `TestEnvironmentDetector`:**

* `test_detects_production_from_environment_variable()`: Sets `ENVIRONMENT=production` and asserts the detector returns `Environment.PRODUCTION` with high confidence.
* `test_detects_development_from_node_env()`: Sets `NODE_ENV=development` and asserts the detector returns `Environment.DEVELOPMENT`.
* `test_falls_back_to_default_with_low_confidence()`: Unsets all relevant environment variables and asserts the detector returns a safe default (e.g., `Environment.DEVELOPMENT`) with a low confidence score.
* `test_feature_context_influences_detection()`: Tests that providing a `FeatureContext` (e.g., `SECURITY_ENFORCEMENT`) correctly influences the detection logic as documented.

---
#### 🔐 **3. Test Suite for `app.infrastructure.cache.encryption.EncryptedCacheLayer`**

This component is a pure, stateless utility whose contract is to perform encryption and decryption. It has no external dependencies and is ideal for straightforward unit testing.

* **Behavior Under Test**: A dictionary serialized and encrypted by `encrypt_cache_data` must be perfectly reconstructed by `decrypt_cache_data`. This is the core "round-trip" guarantee.
* **Isolation Strategy**: No mocking is needed. The test verifies the component's internal logic directly.

**Recommended Test Cases for `TestEncryptedCacheLayer`:**

* `test_encryption_decryption_round_trip_succeeds()`: Encrypts a sample dictionary, decrypts the result, and asserts the reconstructed dictionary is identical to the original.
* `test_decrypting_with_wrong_key_fails()`: Creates two `EncryptedCacheLayer` instances with different keys. Encrypts data with the first and asserts that calling `decrypt_cache_data` with the second key raises an `InvalidToken` exception from the `cryptography` library.

### New Integration Tests to Add

Your integration testing philosophy is to verify the **collaborative behavior** of internal components, testing from the "outside-in" against a high-fidelity environment. The new security contracts introduce critical new collaborations that must be verified.

---
#### 🚀 **1. Test Suite for Application Startup Security Validation**

This is the most critical new integration test. It verifies that the main FastAPI application correctly collaborates with the `RedisSecurityValidator` at startup to enforce the fail-fast security policy.

* **Seam Under Test**: Application Startup ↔ `RedisSecurityValidator`.
* **Testing Strategy**: This is an "outside-in" test. We will use FastAPI's `TestClient` to attempt to initialize the entire application under different environment variable configurations and assert on the outcome.
* **Infrastructure Needs**: `monkeypatch` to control environment variables. No live Redis is needed, as the validation happens before a connection is attempted.

**Recommended Test Cases for `TestAppStartupSecurityValidation`:**

* `test_app_startup_fails_in_production_with_insecure_redis_url()`:
    1.  **Given**: `monkeypatch` sets `ENVIRONMENT=production` and `CACHE_REDIS_URL="redis://..."`.
    2.  **When**: The FastAPI `TestClient` is initialized for the app.
    3.  **Then**: A `ConfigurationError` is raised, preventing the application from starting.
* `test_app_startup_succeeds_in_development_with_insecure_redis_url()`:
    1.  **Given**: `monkeypatch` sets `ENVIRONMENT=development` and `CACHE_REDIS_URL="redis://..."`.
    2.  **When**: The `TestClient` is initialized.
    3.  **Then**: The application starts successfully without raising an exception.

---
#### 🔄 **2. Test Suite for Secure Cache Creation and Fallback**

This test verifies the collaboration between the `CacheManager` (or `GenericRedisCache.create_secure`) and the `EnvironmentDetector` to provide either a secure Redis connection or a graceful fallback.

* **Seam Under Test**: `CacheManager` ↔ `EnvironmentDetector` ↔ Secure Redis Instance.
* **Testing Strategy**: We will test the `CacheManager`'s observable behavior. When a real, secure Redis instance is available, it should connect. When it's not, it should fall back to `InMemoryCache` without crashing.
* **Infrastructure Needs**: A secure `Testcontainers` Redis instance (as outlined in the previous response for fixing your existing integration tests) and `monkeypatch`.

**Recommended Test Cases for `TestSecureCacheCreationAndFallback`:**

* `test_cache_manager_connects_to_secure_redis_in_production()`:
    1.  **Given**: A secure Redis container is running and `monkeypatch` sets `ENVIRONMENT=production`.
    2.  **When**: A `CacheManager` instance is created.
    3.  **Then**: The manager's active cache is an instance of `GenericRedisCache` and its health check reports a successful, secure connection.
* `test_cache_manager_falls_back_to_memory_when_redis_is_unavailable()`:
    1.  **Given**: No Redis container is running.
    2.  **When**: A `CacheManager` instance is created.
    3.  **Then**: The manager's active cache is an instance of `InMemoryCache` and the operation completes without raising an exception. This verifies the "Graceful Fallback" requirement from the PRD.