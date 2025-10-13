---
description:
globs:
alwaysApply: false
---
# Parallel Testing Best Practices

## **Default Test Execution Strategy**

- **Always use parallel execution by default** for faster feedback cycles
- **Configure pytest-xdist** for optimal performance across test suites
- **Implement proper environment isolation** to prevent test interference
- **Use appropriate worker distribution strategies** based on test characteristics

## **Default Pytest Configuration**

```ini
# pytest.ini - Default parallel configuration
[tool:pytest]
addopts = 
    -n auto
    --dist worksteal
    -v
    --tb=short
    --strict-markers
    --strict-config
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

## **Environment Isolation Patterns**

### **✅ DO: Use monkeypatch for environment variables**
```python
@pytest.fixture
def service_with_api_key(mock_cache_service, mock_settings, monkeypatch):
    """Properly isolated environment setup."""
    # Use monkeypatch for better parallel test isolation
    monkeypatch.setenv('API_KEY', 'test-key')
    monkeypatch.setenv('ENVIRONMENT', 'test')
    return ServiceClass(settings=mock_settings, cache=mock_cache_service)
```

### **❌ DON'T: Use patch.dict context managers in fixtures**
```python
@pytest.fixture
def service_with_api_key(mock_cache_service, mock_settings):
    """BAD: Context exits before test runs in parallel execution."""
    with patch.dict(os.environ, {'API_KEY': 'test-key'}):
        return ServiceClass(settings=mock_settings, cache=mock_cache_service)
```

### **✅ DO: Use class-level monkeypatch for shared setup**
```python
class TestServiceFeatures:
    @pytest.fixture
    def isolated_service(self, mock_dependencies, monkeypatch):
        # Each test class gets isolated environment
        monkeypatch.setenv('FEATURE_FLAG', 'enabled')
        return ServiceClass()
```

## **Parallel Test Commands**

### **Default Development Testing**
```bash
# Fast feedback with optimal worker count
pytest -n auto --dist worksteal

# Specific test file with parallel execution
pytest tests/test_specific.py -n 4 --dist worksteal

# Coverage with parallel execution
pytest -n auto --cov=app --cov-report=html
```

### **CI/CD Pipeline Testing**
```bash
# Maximum parallelization for CI
pytest -n $(nproc) --dist worksteal --maxfail=5

# With detailed reporting for CI
pytest -n auto --dist worksteal --junitxml=test-results.xml --cov-report=xml
```

### **Debug Mode (Sequential)**
```bash
# Use sequential execution for debugging
pytest -s -vv --tb=long

# Single test with detailed output
pytest tests/test_file.py::TestClass::test_method -s -vv
```

## **Worker Distribution Strategies**

- **`--dist worksteal`** (Default): Dynamic load balancing, best for mixed test durations
- **`--dist loadscope`**: Distribute by test scope (class, module), good for setup/teardown optimization
- **`--dist loadfile`**: Distribute by file, useful for file-level isolation requirements

## **Fixture Design for Parallel Execution**

### **✅ DO: Design stateless fixtures**
```python
@pytest.fixture
def clean_database(monkeypatch):
    """Each test gets a clean, isolated database state."""
    # Use unique test database per worker
    test_db = f"test_db_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{test_db}")
    
    # Setup
    create_test_database(test_db)
    yield test_db
    
    # Cleanup
    cleanup_test_database(test_db)
```

### **✅ DO: Use worker-specific resources**
```python
@pytest.fixture(scope="session")
def worker_specific_port(worker_id):
    """Assign unique ports per worker to avoid conflicts."""
    if worker_id == "master":
        return 8000
    # Extract worker number and offset port
    worker_num = int(worker_id.replace("gw", ""))
    return 8000 + worker_num + 1
```

### **❌ DON'T: Share mutable state between tests**
```python
# BAD: Global state that can cause race conditions
_global_test_state = {}

@pytest.fixture
def shared_state():
    return _global_test_state  # This will cause issues in parallel
```

## **When to Use Sequential Testing**

### **Use `-n 0` or sequential execution for:**
- **Debugging failing tests** with detailed tracebacks
- **Tests that require specific resource ordering** (e.g., database migrations)
- **Integration tests with external dependencies** that can't be parallelized
- **Performance/timing-sensitive tests** where parallelization affects results

```python
# Mark tests that must run sequentially
@pytest.mark.no_parallel
def test_database_migration_order():
    """This test requires sequential execution."""
    pass

# In pytest.ini, configure to skip parallel for specific markers:
# addopts = -n auto --dist worksteal -m "not no_parallel"
```

## **Performance Optimization**

### **Test Organization**
- **Group fast tests together** for better load balancing
- **Separate slow integration tests** into dedicated modules
- **Use appropriate test scopes** (function, class, module, session)

### **Resource Management**
```python
@pytest.fixture(scope="session")
def expensive_setup():
    """Share expensive setup across all tests in the session."""
    setup_result = perform_expensive_operation()
    yield setup_result
    cleanup_expensive_operation(setup_result)

@pytest.fixture
def test_specific_data(expensive_setup):
    """Build on shared setup for individual tests."""
    return create_test_data_from(expensive_setup)
```

## **Common Parallel Testing Patterns**

### **Service Initialization Pattern**
```python
class TestServiceClass:
    @pytest.fixture
    def service(self, mock_dependencies, monkeypatch):
        # Environment isolation
        monkeypatch.setenv('SERVICE_ENV', 'test')
        
        # Mock external dependencies
        with patch('app.services.external_api.ExternalAPI') as mock_api:
            mock_api.return_value.method.return_value = "mocked_response"
            
            service = ServiceClass(dependencies=mock_dependencies)
            return service
```

### **Database Testing Pattern**
```python
@pytest.fixture
def isolated_db(monkeypatch):
    """Each test gets a completely isolated database."""
    db_name = f"test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_name}")
    
    # Initialize schema
    init_test_database(db_name)
    yield db_name
    
    # Cleanup
    drop_test_database(db_name)
```

## **Troubleshooting Parallel Test Issues**

### **Common Issues and Solutions**

1. **Environment Variable Conflicts**
   - Solution: Use `monkeypatch.setenv()` instead of `patch.dict(os.environ)`

2. **Port/Resource Conflicts**
   - Solution: Use worker-specific ports/resources with `worker_id` fixture

3. **File System Conflicts**
   - Solution: Use temporary directories with worker-specific paths

4. **Race Conditions in Shared Resources**
   - Solution: Use proper locking or worker-specific resources

### **Debug Commands**
```bash
# Run with verbose worker output
pytest -n 4 --dist worksteal -v --tb=short

# Test specific file sequentially for comparison
pytest tests/problematic_test.py -s -vv

# Run with single worker to isolate issues
pytest -n 1 --dist worksteal
```

## **Integration with CI/CD**

### **GitHub Actions Example**
```yaml
- name: Run parallel tests
  run: |
    pytest -n auto --dist worksteal \
           --cov=app \
           --cov-report=xml \
           --junitxml=test-results.xml \
           --maxfail=10
```

### **Local Development Script**
```bash
#!/bin/bash
# scripts/test-parallel.sh
set -e

echo "Running parallel tests..."
pytest -n auto --dist worksteal --tb=short

echo "Running coverage report..."
pytest -n auto --cov=app --cov-report=html --cov-report=term-missing
```

---

**Key Takeaways:**
- Use parallel execution as the default for faster feedback
- Always use `monkeypatch` for environment isolation in fixtures
- Design tests to be stateless and independent
- Use sequential execution only for debugging or special cases
- Optimize resource usage with proper fixture scoping
