# Integration Test Plan: Cryptography Library Unavailability

## Overview

This integration test plan covers scenarios where the `cryptography` library is not available in the Python environment. These tests verify that the application degrades gracefully and provides helpful error messages when this mandatory dependency is missing.

## Why Integration Tests?

**Unit-level mocking of library availability is problematic because:**
- Mocking `builtins.__import__` causes pytest internal errors during test failure reporting
- Mocking `sys.modules` doesn't prevent import-time module loading
- The cryptography library is imported at module load time, before test fixtures run
- Attempting to simulate missing libraries at unit level creates import-time side effects

**Integration tests solve this by:**
- Running in a separate Python environment where cryptography is actually uninstalled
- Testing real import behavior without mocking interference
- Verifying actual error messages users would see in production

## Test Scenarios to Implement

### 1. Cache Encryption Component

**File:** `tests/integration/startup/test_cache_encryption_cryptography_unavailable.py`

#### Test: Missing Cryptography Error Message Quality
```python
def test_encrypted_cache_initialization_without_cryptography():
    """
    Test that EncryptedCacheLayer provides helpful error when cryptography is missing.

    Environment:
        - Python environment WITHOUT cryptography package installed

    Scenario:
        Given: cryptography library is not installed
        When: EncryptedCacheLayer(encryption_key="any-key") is initialized
        Then: ConfigurationError is raised
        And: Error message includes "Install with: pip install cryptography"
        And: Error message indicates "cryptography library is required"
        And: Error message states "This is a mandatory dependency for secure Redis operations"

    Setup:
        - Use Docker container or virtualenv without cryptography
        - Import app.infrastructure.cache.encryption
        - Attempt initialization

    Assertions:
        - Exception type is ConfigurationError
        - Error message contains installation command
        - Error message is helpful and actionable
    """
```

### 2. Redis Security Validation

**File:** `tests/integration/startup/test_redis_security_cryptography_unavailable.py`

#### Test: TLS Certificate Validation Warning
```python
def test_tls_certificate_validation_warns_without_cryptography():
    """
    Test that TLS validation adds warning when cryptography is unavailable.

    Environment:
        - Python environment WITHOUT cryptography package installed

    Scenario:
        Given: Certificate files exist
        And: cryptography library is not installed
        When: validate_tls_certificates() is called
        Then: result["valid"] is True (file validation still works)
        And: result["warnings"] contains "cryptography library not available"
        And: Warning indicates "limited validation capability"
        And: No certificate expiration information is available

    Setup:
        - Create temporary certificate files
        - Use environment without cryptography
        - Import app.infrastructure.startup.redis_security

    Assertions:
        - Basic file validation succeeds
        - Warning about limited capability is present
        - No advanced certificate parsing occurs
    """
```

#### Test: Encryption Key Validation Failure
```python
def test_encryption_key_validation_fails_without_cryptography():
    """
    Test that encryption key validation fails when cryptography is unavailable.

    Environment:
        - Python environment WITHOUT cryptography package installed

    Scenario:
        Given: Valid Fernet encryption key is provided
        And: cryptography library is not installed
        When: validate_encryption_key() is called
        Then: result["valid"] is False
        And: result["errors"] contains "cryptography library not available"
        And: Error indicates "cannot be validated"

    Setup:
        - Use valid base64-encoded Fernet key
        - Use environment without cryptography
        - Import app.infrastructure.startup.redis_security

    Assertions:
        - Validation fails (valid=False)
        - Error message is clear about missing library
        - Error indicates encryption cannot be validated
    """
```

## Implementation Approach

### Option 1: Docker-Based Integration Tests (Recommended)

Create a separate Docker container for integration tests without cryptography:

```dockerfile
# tests/integration/docker/Dockerfile.no-cryptography
FROM python:3.13-slim

# Install all dependencies EXCEPT cryptography
COPY requirements.txt /tmp/
RUN pip install $(grep -v cryptography /tmp/requirements.txt)

# Copy test code
COPY tests/integration /tests/integration
COPY app /app

WORKDIR /tests/integration
CMD ["pytest", "startup/", "-v", "--tb=short"]
```

**Run with:**
```bash
docker build -f tests/integration/docker/Dockerfile.no-cryptography -t integration-no-crypto .
docker run integration-no-crypto
```

### Option 2: Virtual Environment Script

Create a script to set up and run tests in isolated environment:

```bash
#!/bin/bash
# tests/integration/scripts/test_without_cryptography.sh

# Create temporary virtual environment
python -m venv /tmp/test-no-crypto
source /tmp/test-no-crypto/bin/activate

# Install dependencies except cryptography
pip install pytest redis fakeredis pydantic
# DO NOT install cryptography

# Run integration tests
PYTHONPATH=/path/to/project/backend pytest tests/integration/startup/ -v

# Cleanup
deactivate
rm -rf /tmp/test-no-crypto
```

### Option 3: Tox Environment

Add to `tox.ini`:

```ini
[testenv:integration-no-crypto]
description = Integration tests without cryptography library
deps =
    pytest
    redis
    fakeredis
    pydantic
    # DO NOT include cryptography
commands =
    pytest tests/integration/startup/ -v --tb=short
setenv =
    PYTHONPATH = {toxinidir}/backend
```

**Run with:**
```bash
tox -e integration-no-crypto
```

## Test Execution

### Manual Testing Alternative

Until integration tests are implemented, these scenarios can be manually verified:

```bash
# 1. Create clean virtual environment
python -m venv /tmp/manual-test
source /tmp/manual-test/bin/activate

# 2. Install project WITHOUT cryptography
pip install -r requirements.txt
pip uninstall cryptography -y

# 3. Test encryption initialization
python -c "from app.infrastructure.cache.encryption import EncryptedCacheLayer; EncryptedCacheLayer('test-key')"
# Should see ConfigurationError with helpful message

# 4. Test validation
python -c "from app.infrastructure.startup.redis_security import RedisSecurityValidator; v = RedisSecurityValidator(); v.validate_encryption_key('test-key')"
# Should see validation failure with library unavailable message

# 5. Cleanup
deactivate
rm -rf /tmp/manual-test
```

## Success Criteria

Integration tests are successful when:

1. **Error Messages Are Helpful**
   - Clear indication of missing library
   - Actionable installation command provided
   - Business impact explained

2. **Graceful Degradation**
   - Application doesn't crash unexpectedly
   - Partial functionality still works where possible
   - Users understand limitations

3. **Test Reliability**
   - Tests run in isolated environment
   - No interference with other tests
   - Consistent, reproducible results

## Migration from Unit Tests

The following unit tests have been marked as skipped and should be migrated:

### Cache Encryption
- `test_initialization.py::test_initialization_without_cryptography_library_raises_error` (line 289)
- `test_initialization.py::test_create_from_env_fails_without_cryptography_library` (line 551)
- `test_error_handling.py::test_missing_cryptography_error_provides_installation_command` (line 1200)

### Redis Security Validation
- `test_component_validation.py::test_validate_tls_certificates_warns_without_cryptography_library` (line 490)
- `test_component_validation.py::test_validate_encryption_key_fails_without_cryptography_library` (line 900)

## References

- **Unit Test Files:**
  - `backend/tests/unit/cache/encryption/test_*.py`
  - `backend/tests/unit/startup/redis_security/test_component_validation.py`

- **Related Documentation:**
  - Testing guide: `docs/guides/testing/INTEGRATION_TESTS.md`
  - Docker setup: `docs/guides/developer/DOCKER.md`

- **Skip Reasons:** All skipped tests reference this plan for implementation guidance
