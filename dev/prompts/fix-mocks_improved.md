# **Prompt for Coding Assistant: Deactivating Pytest Fixture Mocks**

You are an expert Python developer assisting with a major refactoring of a pytest test suite.

## **Goal**

Your task is to systematically "deactivate" a specific list of pytest fixtures that are being phased out. This deactivation will cause any test that relies on these old mocks to be explicitly skipped, clearly marking them for future refactoring.

## **Background Context**

We are refactoring our test suite to eliminate brittle mocks of internal components. We are moving towards a more robust testing strategy that uses real "fake" implementations (like an in-memory version of a service) and higher-level integration tests. The mocks listed below are considered internal to the app.infrastructure.cache component and must be deactivated.

## **Precise Instructions**

For each fixture in the "Target Fixtures" list below, you must perform the following **exact** modifications to its corresponding conftest.py file:

1. Modify the Docstring: Add the following line as the very first line inside the fixture's docstring:  
   DEACTIVATED: This mock is being phased out in favor of real fakes or integration tests.  
2. Insert Skip Code: Add the following line of code as the very first line of executable code inside the fixture's function body:  
   pytest.skip("This test relies on the outdated '{fixture_name}' fixture.")  
   * **Important:** You must replace {fixture_name} with the actual name of the fixture you are modifying. For example, for mock_generic_redis_cache, the line would be pytest.skip("This test relies on the outdated 'mock_generic_redis_cache' fixture.").  
3. **Preserve Original Code:** Do NOT delete or comment out the original code within the fixture. It should remain as is, but it will now be unreachable because of the pytest.skip() call you added.

### **Example**

**Original Fixture:**

@pytest.fixture  
def mock_generic_redis_cache():  
    """  
    Mock GenericRedisCache for testing inheritance and cache operations behavior.  
    ...  
    """  
    from app.infrastructure.cache.redis_generic import GenericRedisCache  
    from unittest.mock import patch  
    # ... original implementation  
    yield mock_instance

**Modified Fixture (Your Target State):**

@pytest.fixture  
def mock_generic_redis_cache():  
    """  
    DEACTIVATED: This mock is being phased out in favor of real fakes or integration tests.

    Mock GenericRedisCache for testing inheritance and cache operations behavior.  
    ...  
    """  
    pytest.skip("This test relies on the outdated 'mock_generic_redis_cache' fixture.")  
    # Original code remains below, now unreachable.  
    from app.infrastructure.cache.redis_generic import GenericRedisCache  
    from unittest.mock import patch  
    # ... original implementation  
    yield mock_instance

## **Target Fixtures and Their Locations**

You must apply the modifications to the following fixtures in their respective files:

**File: backend/tests/infrastructure/cache/conftest.py**

* mock_generic_redis_cache  
* mock_cache_factory  
* mock_memory_cache  
* mock_performance_monitor  
* mock_validation_error  
* mock_configuration_error  
* mock_infrastructure_error

**File: backend/tests/infrastructure/cache/factory/conftest.py**

* mock_ai_response_cache

**File: backend/tests/infrastructure/cache/ai_config/conftest.py**

* mock_validation_result

**File: backend/tests/infrastructure/cache/cache_presets/conftest.py**

* mock_validation_result_with_errors  
* mock_cache_validator  
* mock_validation_result

**File: backend/tests/infrastructure/cache/config/conftest.py**

* mock_validation_result

**File: backend/tests/infrastructure/cache/redis_ai/conftest.py**

* mock_parameter_mapper  
* mock_parameter_mapper_with_validation_errors  
* mock_key_generator  
* mock_redis_connection_failure

**File: backend/tests/infrastructure/cache/redis_generic/conftest.py**

* mock_security_config  
* mock_tls_security_config  
* mock_callback_registry

## **What Not to Do**

* Do NOT modify any other fixtures or any files not listed above.  
* Do NOT alter the logic of the original code within the fixtures.  
* Do NOT change any imports outside of what is necessary for pytest.skip().