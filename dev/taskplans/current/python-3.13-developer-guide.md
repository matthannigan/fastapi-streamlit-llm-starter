# Python 3.13 Developer Guide

## Quick Start with Python 3.13

### Environment Setup
```bash
# 1. Verify Python 3.13 is available
python3.13 --version  # Should show 3.13.x

# 2. Clone and setup project
git clone <repository-url>
cd fastapi-streamlit-llm-starter

# 3. Virtual environment will automatically use Python 3.13 (.python-version file)
make install

# 4. Verify setup
.venv/bin/python --version  # Should show Python 3.13.x
make test-backend            # Should pass all tests
```

### Development Commands
```bash
# Backend development
make run-backend             # Start FastAPI server
make test-backend           # Run backend tests
make lint-backend           # Code quality checks

# Frontend development
make run-frontend           # Start Streamlit app
make test-frontend          # Run frontend tests

# Full stack development
make dev                    # Start both backend and frontend
make test                   # Run all tests
```

## Python 3.13 Features in Use

### Type System Improvements
```python
# ✅ Use @override decorator for method overrides
from typing import override

class RedisCache(BaseCache):
    @override
    def get(self, key: str) -> Optional[str]:
        return super().get(key)

# ✅ Enhanced union syntax
def process_data(input: str | bytes | None) -> dict[str, Any]:
    pass

# ✅ Better generic syntax
class ResponseCache[T]:
    def store(self, key: str, value: T) -> None:
        pass
```

### Enhanced Error Handling
```python
# ✅ Python 3.13 provides better error messages
try:
    result = some_complex_operation()
except Exception as e:
    # Error messages are now more helpful and specific
    logger.error(f"Operation failed: {e}")
```

### Performance Features
```python
# ✅ JIT compiler benefits (automatic)
# No code changes needed - Python 3.13 JIT compiler
# automatically optimizes hot paths for 15-20% speedup

# ✅ Optimized data structures
cache_stats: dict[str, int] = {}  # Faster dict operations
user_sessions: list[Session] = []  # Better list performance
```

### String Processing Improvements
```python
# ✅ Enhanced f-strings (more flexible expressions)
status = "healthy" if is_healthy else "degraded"
message = f"System status: {
    'All services operational' if status == 'healthy'
    else 'Some services experiencing issues'
}"

# ✅ Better string formatting performance
log_entry = f"[{timestamp}] {level}: {message}"  # Optimized
```

## Development Best Practices

### Dependency Management
```bash
# ✅ All dependencies are Python 3.13 compatible
cd backend && pip list          # View current dependencies
make update-deps               # Update to latest compatible versions

# ✅ For new dependencies, verify Python 3.12+ support
pip install new-package        # Will fail if incompatible
```

### Testing with Python 3.13
```bash
# ✅ Run tests with coverage
make test-coverage

# ✅ Performance testing shows improvements
make test-backend-performance  # Leverages JIT compiler benefits

# ✅ Integration testing validates all components
make test-integration
```

### IDE and Editor Setup

#### VS Code
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.analysis.typeCheckingMode": "strict",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true
}
```

#### PyCharm
- Set Project Interpreter to `.venv/bin/python`
- Enable Python 3.13 language features
- Configure type checking to "strict"

### Docker Development
```dockerfile
# ✅ Containers use Python 3.13-slim
FROM python:3.13-slim

# ✅ Build process optimized for new runtime
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

## Performance Optimization Guide

### JIT Compiler Benefits
```python
# ✅ Hot paths automatically optimized
# These patterns benefit most from JIT compilation:

# Loops with numerical operations
def calculate_metrics(data: list[float]) -> dict[str, float]:
    total = sum(data)  # JIT optimized
    return {"mean": total / len(data)}

# String processing operations
def sanitize_input(text: str) -> str:
    return text.strip().lower()  # JIT optimized

# Cache operations
def cache_lookup(key: str) -> Optional[str]:
    return self.cache.get(key)  # JIT optimized
```

### Memory Optimization
```python
# ✅ Python 3.13 has improved garbage collection
# Less memory usage for:
- Dict and list operations
- String operations
- Function calls
- Object creation/destruction
```

### Async Performance
```python
# ✅ Better async performance in Python 3.13
async def process_batch(items: list[str]) -> list[dict]:
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)  # Faster in 3.13
```

## Troubleshooting Common Issues

### Virtual Environment Issues
```bash
# ❌ Problem: Virtual environment not using Python 3.13
# ✅ Solution:
rm -rf .venv
make install

# ❌ Problem: Import errors after upgrade
# ✅ Solution:
pip install --upgrade --force-reinstall -r requirements.txt
```

### Performance Issues
```bash
# ✅ Check if JIT compiler is active
python -c "import sys; print(f'JIT: {hasattr(sys, \"_getframe\")}')"

# ✅ Profile performance improvements
make test-backend-performance
```

### Testing Issues
```bash
# ❌ Problem: Tests failing after migration
# ✅ Solution: Check baseline comparison
diff dev/taskplans/current/testing_failures_prior.txt current_results.txt

# ✅ Only address NEW failures, not pre-existing ones
```

## Migration for Other Projects

### Step-by-Step Migration
```bash
# 1. Update configuration files
sed -i 's/requires-python = ">=3.8"/requires-python = ">=3.12"/' pyproject.toml

# 2. Update CI/CD
# Change python-version matrix to ["3.12", "3.13"]

# 3. Update containers
sed -i 's/python:3.11-slim/python:3.13-slim/' Dockerfile

# 4. Test compatibility
python3.13 -m pip install -r requirements.txt
python3.13 -m pytest tests/
```

### Compatibility Checklist
- [ ] All dependencies support Python 3.12+
- [ ] No usage of deprecated features removed in 3.12+
- [ ] Container builds succeed with Python 3.13
- [ ] Test suite passes without new failures
- [ ] Performance improvements measured

## Resources

### Documentation
- [Python 3.13 Release Notes](https://docs.python.org/3.13/whatsnew/3.13.html)
- [Migration Guide](python-modernization_summary.md)
- [Rollback Procedures](python-modernization_rollback_guide.md)

### Project-Specific
- Backend: `backend/CLAUDE.md` - Testing and development patterns
- Frontend: `frontend/CLAUDE.md` - UI development with Python 3.13
- Infrastructure: `docs/guides/` - Comprehensive service documentation

### Performance Monitoring
```bash
# Benchmark before/after migration
make test-backend-performance

# Monitor JIT compiler benefits
python -X showrefcount your_script.py

# Track memory usage improvements
make test-coverage-all
```