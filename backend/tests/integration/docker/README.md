# Docker-Based Integration Tests

This directory contains Docker infrastructure for running integration tests in isolated environments with specific dependency configurations.

## Cryptography Unavailability Tests

### Overview

These tests verify that the application gracefully degrades and provides helpful error messages when the `cryptography` library is unavailable. This is critical for:

- **Deployment troubleshooting**: Ensuring developers get clear error messages
- **Dependency validation**: Verifying cryptography is properly required
- **Graceful degradation**: Testing fallback behavior when libraries are missing

### Why Docker-Based Testing?

**Unit-level mocking of library availability is problematic:**
- Mocking `builtins.__import__` causes pytest internal errors during test failure reporting
- Mocking `sys.modules` doesn't prevent import-time module loading
- The cryptography library is imported at module load time, before test fixtures run
- Attempting to simulate missing libraries at unit level creates import-time side effects

**Docker integration tests solve this by:**
- Running in a separate Python environment where cryptography is actually uninstalled
- Testing real import behavior without mocking interference
- Verifying actual error messages users would see in production

## Quick Start

### Run All Cryptography Unavailability Tests

```bash
# From project root
./backend/tests/integration/docker/run-no-cryptography-tests.sh
```

This script:
1. Builds a Docker image with all dependencies EXCEPT cryptography
2. Runs integration tests in the isolated environment
3. Reports test results

### Run Tests Manually with Docker

```bash
# From project root
cd backend/tests/integration/docker

# Build the image
docker build -f Dockerfile.no-cryptography -t fastapi-integration-no-crypto:latest ../../..

# Run the tests
docker run --rm fastapi-integration-no-crypto:latest

# Or run specific tests
docker run --rm fastapi-integration-no-crypto:latest \
  pytest tests/integration/startup/test_cache_encryption_cryptography_unavailable.py -v
```

### Run Tests with Docker Compose

```bash
# From docker directory
docker-compose -f docker-compose.no-cryptography.yml up --build

# Cleanup
docker-compose -f docker-compose.no-cryptography.yml down
```

## Test Files

### Cache Encryption Tests
**File**: `../test_cache_encryption_cryptography_unavailable.py`

Tests that verify:
- EncryptedCacheLayer raises ConfigurationError when cryptography is missing
- Error message includes installation command: `pip install cryptography`
- Error message explains business impact (mandatory for secure Redis operations)
- Error context includes helpful metadata for troubleshooting

**Key Test Scenarios:**
- `test_encrypted_cache_initialization_without_cryptography`: Main error handling test
- `test_encryption_error_message_is_actionable`: Error message quality validation
- `test_error_includes_installation_command`: Ensures copy-paste ready guidance

### Redis Security Validation Tests
**File**: `../test_redis_security_cryptography_unavailable.py`

Tests that verify:
- TLS certificate validation provides warnings when cryptography unavailable
- Basic file validation still works without cryptography
- Encryption key validation fails with clear error messages
- Comprehensive validation aggregates cryptography warnings

**Key Test Scenarios:**
- `test_tls_certificate_validation_warns_without_cryptography`: Graceful degradation for TLS
- `test_encryption_key_validation_fails_without_cryptography`: Validation failure handling
- `test_comprehensive_validation_includes_cryptography_warnings`: End-to-end validation

## Docker Infrastructure

### Dockerfile.no-cryptography

The main Dockerfile that:
1. Uses Python 3.13-slim base image
2. Installs Poetry for dependency management
3. Removes cryptography from pyproject.toml during build
4. Installs all other dependencies
5. Sets up test environment

**Key Features:**
- Modifies pyproject.toml to exclude cryptography: `sed -i '/^cryptography = /d' pyproject.toml`
- Installs main and test dependencies: `poetry install --only main,test`
- Sets PYTHONPATH for proper module imports
- Runs tests with coverage disabled (isolated environment)

### docker-compose.no-cryptography.yml

Docker Compose configuration for easier test execution:
- Builds from project root context
- Mounts test results volume
- Configures test network
- Sets environment variables

### run-no-cryptography-tests.sh

Convenience script that:
- Builds Docker image with clear progress output
- Runs tests with proper volume mounts
- Provides colored output for test results
- Returns appropriate exit codes

**Usage:**
```bash
./run-no-cryptography-tests.sh
```

## Test Execution Requirements

### Environment Prerequisites

These tests should ONLY run in environments where cryptography is NOT installed:
- Docker container (recommended - use provided scripts)
- Isolated virtual environment (manual setup)
- CI/CD pipeline with custom environment

### Automatic Skipping

The tests are marked to skip if cryptography IS available:

```python
pytestmark = pytest.mark.skipif(
    CRYPTOGRAPHY_AVAILABLE,
    reason="Tests require cryptography library to be UNAVAILABLE. "
    "Run via Docker: ./backend/tests/integration/docker/run-no-cryptography-tests.sh"
)
```

This prevents accidental execution in standard test environments.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests - No Cryptography

on: [push, pull_request]

jobs:
  test-no-crypto:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build \
            -f backend/tests/integration/docker/Dockerfile.no-cryptography \
            -t test-no-crypto:${{ github.sha }} \
            .

      - name: Run tests
        run: |
          docker run --rm test-no-crypto:${{ github.sha }}
```

### GitLab CI Example

```yaml
test-no-cryptography:
  image: docker:latest
  services:
    - docker:dind
  script:
    - cd backend/tests/integration/docker
    - docker build -f Dockerfile.no-cryptography -t test-no-crypto .
    - docker run --rm test-no-crypto
  only:
    - merge_requests
    - main
```

## Troubleshooting

### Issue: Docker build fails

**Problem**: Docker build fails with dependency errors

**Solution**: Ensure you're running from project root:
```bash
# From project root (not from docker directory)
docker build -f backend/tests/integration/docker/Dockerfile.no-cryptography .
```

### Issue: Tests are skipped

**Problem**: Tests show as skipped when running locally

**Solution**: This is expected! These tests only run when cryptography is NOT installed. Use Docker:
```bash
./backend/tests/integration/docker/run-no-cryptography-tests.sh
```

### Issue: Import errors in tests

**Problem**: Tests fail with import errors

**Solution**: Check PYTHONPATH in Dockerfile:
```dockerfile
ENV PYTHONPATH=/app/backend:/app/shared
```

### Issue: Permission denied on run script

**Problem**: Cannot execute run-no-cryptography-tests.sh

**Solution**: Make script executable:
```bash
chmod +x backend/tests/integration/docker/run-no-cryptography-tests.sh
```

## Manual Testing Alternative

For manual verification without Docker:

```bash
# 1. Create clean virtual environment
python -m venv /tmp/test-no-crypto
source /tmp/test-no-crypto/bin/activate

# 2. Install dependencies WITHOUT cryptography
cd backend
pip install pytest redis fakeredis pydantic fastapi pydantic-ai httpx
# DO NOT: pip install cryptography

# 3. Run tests
export PYTHONPATH=/path/to/project/backend:/path/to/project/shared
pytest tests/integration/startup/test_*_cryptography_unavailable.py -v

# 4. Cleanup
deactivate
rm -rf /tmp/test-no-crypto
```

## Test Coverage

These integration tests validate:

✅ **Cache Encryption Component**
- Error handling when cryptography unavailable
- Error message quality and actionability
- Installation guidance for developers

✅ **Redis Security Validation**
- TLS certificate validation graceful degradation
- Encryption key validation failure handling
- Comprehensive security validation with warnings

✅ **Error Message Quality**
- Clear indication of missing library
- Actionable installation commands
- Business impact explanation
- Helpful troubleshooting context

## Reference Documentation

- **Test Plan**: `../TEST_PLAN_cryptography_unavailable.md`
- **Integration Testing Philosophy**: `docs/guides/testing/INTEGRATION_TESTS.md`
- **Cache Encryption**: `backend/app/infrastructure/cache/encryption.py`
- **Redis Security**: `backend/app/core/startup/redis_security.py`

## Contributing

When adding new cryptography-dependent features:

1. **Add integration test** in this directory for unavailability scenario
2. **Update Dockerfile** if new dependencies are added
3. **Update this README** with new test scenarios
4. **Verify tests pass** using `run-no-cryptography-tests.sh`
5. **Document error messages** in test plan

## Support

For issues or questions:
- Check test plan: `../TEST_PLAN_cryptography_unavailable.md`
- Review test output: Docker provides detailed error messages
- Verify environment: Ensure cryptography is actually unavailable in test environment
