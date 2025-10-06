# Integration Tests

## Running Integration Tests

Integration tests should be run **serially** (not in parallel) to avoid race conditions from shared global state.

### Recommended Commands

```bash
# From backend/ directory
PYTHONPATH=$PWD ../.venv/bin/python -m pytest tests/integration/ -n 0

# From project root using Makefile
make test-backend-integration
```

### Why Serial Execution?

Integration tests manipulate:
- Environment variables
- Global singleton instances (`environment_detector`)
- Docker containers
- Shared cache state

Running in parallel with pytest-xdist (`-n auto`) causes race conditions where:
- One test's environment changes affect another test in a different worker
- Global instances cache stale state from previous tests
- Tests pass individually but fail intermittently when run together

### Performance Trade-off

- **Serial (`-n 0`)**: Slower (~6-8s) but 100% reliable
- **Parallel (`-n auto`)**: Faster (~4-5s) but 0-15 failures per run (flaky)

Integration tests are a small subset of the test suite, so the serial execution overhead is acceptable for reliability.

### Test Organization

```
tests/integration/
├── auth/          # Authentication integration tests
├── cache/         # Cache infrastructure integration tests (forced serial via conftest hook)
├── environment/   # Environment detection integration tests
├── health/        # Health check integration tests
└── startup/       # Application startup integration tests
```

### Troubleshooting

**Error**: "🔒 SECURITY ERROR: Failed to initialize mandatory security features"

**Cause**: Test running without `ENVIRONMENT` set or with stale environment detection

**Solution**:
1. Ensure running with `-n 0` (serial)
2. Check `tests/integration/cache/conftest.py` has autouse fixture setting `ENVIRONMENT='testing'`
3. Verify no other test is unsetting `ENVIRONMENT` during execution

**Error**: Tests pass individually but fail when run together

**Cause**: Shared state pollution from parallel execution

**Solution**: Always run integration tests with `-n 0`
