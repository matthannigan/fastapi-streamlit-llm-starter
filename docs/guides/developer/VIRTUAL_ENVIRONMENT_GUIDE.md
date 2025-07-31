# Virtual Environment Management

This document explains the enhanced virtual environment management implemented in the FastAPI-Streamlit-LLM starter template.

## Overview

The project now includes automatic virtual environment management through an enhanced Makefile that:

- **Automatically detects Python executable** (`python3` or `python`)
- **Creates project-level virtual environment** (`.venv/`)
- **Handles dependency installation** in the virtual environment
- **Provides Docker-free testing** options
- **Manages environment awareness** (Docker, venv, or system Python)

## Quick Start

```bash
# Create virtual environment and install all dependencies
make install

# Run tests without Docker dependency
make test-local

# Run all tests (includes Docker integration if available)
make test

# Clean up virtual environment
make clean-all
```

## Virtual Environment Features

### Automatic Python Detection

The Makefile automatically finds the best Python executable:

```makefile
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)
```

### Environment Awareness

The system detects the current environment:

- **Docker Environment**: Uses `python` directly
- **Virtual Environment**: Uses `.venv/bin/python`
- **System Python**: Uses detected Python executable

### Smart Command Selection

```makefile
# Use venv python if available and not in Docker, otherwise use system python
ifeq ($(IN_DOCKER),1)
    PYTHON_CMD := python
else ifeq ($(wildcard $(VENV_PYTHON)),$(VENV_PYTHON))
    PYTHON_CMD := $(VENV_PYTHON)
else
    PYTHON_CMD := $(PYTHON)
endif
```

## Available Commands

### Setup Commands

| Command | Description |
|---------|-------------|
| `make venv` | Create virtual environment only |
| `make install` | Create venv and install all dependencies |

### Testing Commands

| Command | Description |
|---------|-------------|
| `make test` | Run all tests (with Docker if available) |
| `make test-local` | Run tests without Docker dependency |
| `make test-backend` | Run backend tests only |
| `make test-frontend` | Run frontend tests only |
| `make test-coverage` | Run tests with coverage report |

### Code Quality Commands

| Command | Description |
|---------|-------------|
| `make lint` | Run code quality checks |
| `make format` | Format code with black and isort |

### Cleanup Commands

| Command | Description |
|---------|-------------|
| `make clean` | Clean generated files |
| `make clean-all` | Clean including virtual environment |

## Manual Virtual Environment Usage

If you prefer to manage the virtual environment manually:

### Activation

```bash
# Activate virtual environment
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

### Deactivation

```bash
# Deactivate virtual environment
deactivate
```

### Direct Usage Without Activation

```bash
# Run Python commands directly
.venv/bin/python -m pytest tests/

# Run backend tests
cd backend
../.venv/bin/python -m pytest tests/ -v

# Run frontend tests
cd frontend
../.venv/bin/python -m pytest tests/ -v
```

## Benefits

### For Developers

1. **No Manual Environment Management**: The Makefile handles everything
2. **Cross-Platform Compatibility**: Works on macOS, Linux, and Windows
3. **Python Version Flexibility**: Automatically detects `python3` or `python`
4. **Docker Independence**: Can run tests without Docker
5. **Consistent Dependencies**: All developers use the same environment

### For CI/CD

1. **Predictable Environment**: Same setup across all environments
2. **Fast Testing**: Local tests don't require Docker
3. **Isolated Dependencies**: No conflicts with system packages
4. **Easy Debugging**: Clear separation of environments

## Troubleshooting

### Common Issues

#### Python Command Not Found

**Problem**: `make install` fails with "python command not found"

**Solution**: Install Python 3.8+ and ensure it's in your PATH

#### Virtual Environment Issues

**Problem**: Tests fail with import errors

**Solution**: 
```bash
make clean-all  # Remove virtual environment
make install    # Recreate and reinstall
```

#### Permission Issues

**Problem**: Cannot create virtual environment

**Solution**: Check directory permissions and ensure you have write access

#### Docker vs Local Testing

**Problem**: Tests behave differently in Docker vs locally

**Solution**: Use `make test-local` for local testing and `make test` for full integration

### Debug Information

To see what Python executable is being used:

```bash
# Check detected Python
make help  # Shows current configuration

# Manual check
command -v python3 || command -v python
```

## Migration from Old Setup

If you're migrating from the previous setup:

1. **Remove old virtual environments**:
   ```bash
   rm -rf backend/.venv frontend/.venv
   ```

2. **Use new setup**:
   ```bash
   make install
   ```

3. **Update your workflow**:
   - Replace `cd backend && python -m pytest` with `make test-backend`
   - Replace manual dependency installation with `make install`
   - Use `make test-local` for Docker-free testing

## Best Practices

1. **Use Makefile commands** instead of manual Python commands
2. **Run `make install`** after pulling new changes
3. **Use `make test-local`** for quick testing during development
4. **Use `make test`** for full integration testing
5. **Run `make clean-all`** if you encounter environment issues

## Integration with IDEs

### VS Code

Add to your VS Code settings:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.terminal.activateEnvironment": true
}
```

### PyCharm

1. Go to Settings → Project → Python Interpreter
2. Add New Interpreter → Existing Environment
3. Select `.venv/bin/python`

### Vim/Neovim

Add to your configuration:

```vim
let g:python3_host_prog = '.venv/bin/python'
```

## Conclusion

The enhanced virtual environment management provides a robust, cross-platform solution for dependency management and testing. It eliminates common setup issues while providing flexibility for both local development and CI/CD environments.

For questions or issues, refer to the main [TESTING.md](TESTING.md) guide or open an issue in the repository. 