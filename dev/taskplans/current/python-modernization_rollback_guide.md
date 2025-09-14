# Python Modernization Rollback Guide

## Overview
This guide provides step-by-step procedures to rollback the Python 3.13 modernization if issues arise.

## Rollback Scenarios

### Scenario 1: Development Environment Issues
**Symptoms**: Local development environment not working with Python 3.13
**Solution**:
```bash
# 1. Change development version
echo "3.11" > .python-version

# 2. Recreate virtual environment
rm -rf .venv
make install

# 3. Verify functionality
make test-backend
```

### Scenario 2: CI/CD Pipeline Issues
**Symptoms**: GitHub Actions failing with Python 3.12/3.13
**Rollback Steps**:
```yaml
# In .github/workflows/test.yml, change:
python-version: ["3.9", "3.10", "3.11"]
# Remove experimental 3.14-dev section
```

### Scenario 3: Complete Rollback to Python 3.11
**Use Case**: Major compatibility issues discovered
**Steps**:

1. **Update Configuration Files**:
```bash
# Update all pyproject.toml files
sed -i 's/requires-python = ">=3.12"/requires-python = ">=3.8"/' pyproject.toml
sed -i 's/requires-python = ">=3.12"/requires-python = ">=3.8"/' backend/pyproject.toml
sed -i 's/requires-python = ">=3.12"/requires-python = ">=3.8"/' frontend/pyproject.toml
sed -i 's/requires-python = ">=3.12"/requires-python = ">=3.8"/' shared/pyproject.toml
```

2. **Rollback Docker Images**:
```bash
# Update backend/Dockerfile
sed -i 's/python:3.13-slim/python:3.11-slim/' backend/Dockerfile

# Update frontend/Dockerfile
sed -i 's/python:3.13-slim/python:3.11-slim/' frontend/Dockerfile
```

3. **Rollback CI/CD**:
```yaml
# In .github/workflows/test.yml
python-version: ["3.9", "3.10", "3.11"]
```

4. **Update Development Environment**:
```bash
echo "3.11" > .python-version
rm -rf .venv
make install
```

## Validation After Rollback

### Test System Functionality
```bash
# 1. Verify basic functionality
make test-backend

# 2. Test infrastructure services
make test-backend-infra

# 3. Test API endpoints
make run-backend
# Test http://localhost:8000/v1/health

# 4. Test containers
make docker-build
make docker-up
```

### Dependency Compatibility Check
```bash
# Check for any Python version conflicts
cd backend && pip check
cd ../frontend && pip check
```

## Modern Python Features to Remove in Rollback

If rolling back to Python < 3.10, remove these features:
- Union syntax with `|` operator (use `Union[A, B]` instead)
- Pattern matching with `match` statements
- Parameter specification variables (`ParamSpec`)

If rolling back to Python < 3.11, also remove:
- Exception groups and `except*` syntax
- `Self` type from `typing_extensions`

If rolling back to Python < 3.12, also remove:
- Generic class syntax without explicit inheritance
- `@typing.override` decorator usage

## Documentation Rollback

Update all documentation references:
```bash
# Update README.md
sed -i 's/Python 3.12+/Python 3.8+/' README.md
sed -i 's/Python 3.13 recommended/Python 3.11 recommended/' README.md

# Update CLAUDE.md
sed -i 's/Python 3.13/Python 3.11/' CLAUDE.md
sed -i 's/Python 3.12+/Python 3.8+/' CLAUDE.md
```

## Commit Strategy for Rollback

```bash
# Create rollback branch
git checkout -b rollback/python-modernization

# Apply rollback changes
# ... perform rollback steps above ...

# Commit changes
git add -A
git commit -m "rollback: Revert Python modernization to 3.11

- Restore Python 3.8+ requirement in all pyproject.toml files
- Rollback Docker images to python:3.11-slim
- Restore CI/CD matrix to Python 3.9-3.11
- Remove Python 3.13 specific features and optimizations

Rollback due to: [REASON]

This rollback maintains all functionality while reverting to
the previous Python version requirements for compatibility."

# Create PR for review
gh pr create --title "Rollback: Python modernization to 3.11" --body "Rollback due to compatibility issues"
```

## Recovery Validation

After rollback, verify these components:
- [ ] Virtual environment recreated successfully
- [ ] All dependencies install without conflicts
- [ ] Backend tests pass (compare against baseline)
- [ ] Frontend tests pass
- [ ] Docker containers build and run
- [ ] API endpoints respond correctly
- [ ] CI/CD pipeline passes
- [ ] No functionality degradation

## Risk Assessment

**Low Risk Rollback**: Development environment only
- Change `.python-version` to 3.11
- Recreate virtual environment
- No code changes needed

**Medium Risk Rollback**: Configuration and containers
- Update pyproject.toml files
- Update Dockerfiles
- Update CI/CD configuration
- Test infrastructure compatibility

**High Risk Rollback**: Code features rollback
- Remove Python 3.13 specific language features
- Update type hints and syntax
- Comprehensive testing required
- Potential performance regression

## Prevention for Future Migrations

- Always maintain rollback documentation
- Test compatibility across version range before deployment
- Use feature flags for gradual rollout
- Maintain baseline test results for comparison
- Document all version-specific features used