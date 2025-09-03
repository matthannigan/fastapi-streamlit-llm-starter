# FastAPI + Streamlit LLM Starter Template AGENTS.md

This file provides guidance to coding assistants and agents when working with code in this repository. Together we are building:

**A comprehensive starter template for building production-ready LLM-powered APIs** showcasing industry best practices, robust architecture patterns, and educational examples.

## Monorepo Structure

- **Root directory**: Contains `.venv/` virtual environment and `Makefile`
  - **All Python commands must account for this virtual environment location**
- **Backend** (`backend/`): Production-ready FastAPI with infrastructure services and domain examples
- **Frontend** (`frontend/`): Production-ready Streamlit with async patterns and comprehensive testing  
- **Shared** (`shared/`): Common Pydantic models for type safety
- **Documentation** (`docs/`): Comprehensive project documentation in Markdown

## Agent File Organization

This `AGENTS.md` file contains **general instructions** for the repository. For specific guidance:

- **Backend development**: `backend/AGENTS.md` - FastAPI, infrastructure services, testing
- **Frontend development**: `frontend/AGENTS.md` - Streamlit patterns, UI customization  
- **Documentation work**: `docs/AGENTS.md` - Documentation standards and maintenance
- **Template customization**: `AGENTS.template-users.md` - Step-by-step customization guide

## Cross-Cutting Development Standards

**Coding Standards:**
- Ensure consistency, maintainability, and reliability across the entire codebase
- Maintain clear architectural boundaries between infrastructure and domain concerns
- Reference: `docs/guides/developer/CODE_STANDARDS.md`
- Reference: `docs/guides/developer/DOCSTRINGS_CODE.md`

**Error Handling:**
- Always use custom exceptions (`ConfigurationError`, `ValidationError`, `InfrastructureError`)
- Reference: `docs/guides/developer/EXCEPTION_HANDLING.md`

**Testing:**
- Follow docstring-driven test development
- Reference: `docs/guides/testing/TESTING.md`
- Reference: `docs/guides/developer/DOCSTRINGS_TESTS.md` 

**API Design:**
- Maintain dual API structure (Public `/v1/`, Internal `/internal/`)
- Reference: `docs/reference/key-concepts/DUAL_API_ARCHITECTURE.md`

**Backend Infrastructure vs Domain Services:**
- Infrastructure Services are reusable template components
- Domain Services are application-specific business logic
- This maintains template reusability while providing clear customization points for developers
- Reference: `docs/reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md`

## Preferred Development Commands

The project includes a comprehensive `Makefile` for common tasks. Access the complete list of commands with `make help`. All Python scripts called from the `Makefile` run from the `.venv` virtual environment automatically.

**Always suggest Makefile commands first:**
```bash
# Installation and startup
make install               # Setup dependencies
make dev                   # Run Docker-based development environment
make run-backend           # Start FastAPI server
make run-frontend          # Start Streamlit app

# Testing and quality
make test-backend          # Backend tests
make test-frontend         # Frontend tests  
make lint-backend          # Backend code quality
make lint-frontend         # Frontend code quality

# See `make help` for complete list of commands
```

### Directory Navigation Issues

**Issue**: `make: *** No rule to make target 'help'. Stop.`
**Agent Solution**: 
```bash
# Check current directory - Makefile is in project root
pwd                           # Should show project root, not backend/
cd ..                        # If in backend/, go to project root
make help                    # Now this will work
```

**Issue**: `(eval):cd:1: no such file or directory: backend`
**Agent Solution**:
```bash
# Verify directory structure
pwd                          # Check where you are
ls -la                       # Look for backend/ directory
# If already in backend/, use relative paths:
../.venv/bin/python -m pytest tests/ -v
```

**Issue**: `command not found: python` or virtual environment not found
**Agent Solution**:
```bash
# Virtual environment is in project root, not backend/
ls -la .venv/bin/python      # From project root
ls -la ../.venv/bin/python   # From backend/ directory

# Use full path if needed:
../.venv/bin/python -m pytest tests/ -v
```

## Testing Philosophy & Organization

**This project follows a behavior-driven testing philosophy:**
- **Test behavior, not implementation** - Focus on external observable behavior
- **Maintainability over exhaustiveness** - High-value tests over comprehensive coverage
- **Mock only at system boundaries** - Minimize mocking to reduce test brittleness
- **Fast feedback loops** - Quick test execution for continuous development

**Reference:** `docs/guides/testing/TESTING.md` for comprehensive testing methodology, patterns, and examples.

**For practical testing guidance, troubleshooting, and detailed commands:**
- **Backend testing**: See `backend/AGENTS.md` 
- **Frontend testing**: See `frontend/AGENTS.md`

## Documentation

**Comprehensive documentation index for `docs/` located at `docs/DOCS_INDEX.md`.**

**📖 Template Documentation:**
- **`docs/README.md`**: Main project overview and quick start guide
- **`docs/get-started/`**: Setup & complete systems integration guide, installation checklist
- **`docs/reference/key-concepts/`**: Infrastructure vs Domain Services, Dual API Architecture
- **`docs/guides/`**: Comprehensive guides (backend, frontend, testing, deployment, customization)
- **`docs/guides/infrastructure/`**: AI, Cache, Monitoring, Resilience, Security services
- **`docs/guides/developer/`**: Authentication, code standards, Docker, documentation guidance

**📚 Technical Deep Dives:**
- **`docs/reference/deep-dives/`**: FastAPI and Streamlit comprehensive technical analysis

**📦 Code Reference (Auto-Generated):**
- **`docs/code_ref/`**: Auto-generated code reference documentation (backend + frontend) - **DO NOT EDIT** these files manually, they are generated via `make code_ref`
- Auto-generated files `./code_ref/**/index.md` correspond to `**/README.md` files throughout the repository structure

## Configuration Management & Environment Variables

**Use preset-based configuration:**
```bash
# Recommended approach
RESILIENCE_PRESET=production
CACHE_PRESET=ai-production

# Avoid individual variables when presets available
```

See recommendations for `development` and `production` configurations in `docs/get-started/ENVIRONMENT_VARIABLES.md`. See `.env.example` for complete variable descriptions.

## Utility Scripts & Tools

**Development and operational scripts (`scripts/` directory):**
- **`run_tests.py`**: Comprehensive test runner with Docker support and parallel execution
- **`test_integration.py`**: End-to-end integration testing across services
- **`validate_resilience_config.py`**: Configuration validation and preset management tools
- **`migrate_resilience_config.py`**: Legacy configuration migration utilities
- **`generate_code_docs.py`**: Automated code documentation generation for `docs/code_ref/`

**All scripts run from project root using `.venv` virtual environment automatically.**

## Important Development Guidelines

- Do what has been asked; nothing more, nothing less
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User

## See Also

- **Backend Development**: `backend/AGENTS.md` for FastAPI-specific guidance
- **Frontend Development**: `frontend/AGENTS.md` for Streamlit and UI development  
- **Documentation Work**: `docs/AGENTS.md` for documentation standards
- **Template Customization**: `AGENTS.template-users.md` for step-by-step customization
- **Complete Documentation**: `docs/DOCS_INDEX.md` for all available guides
