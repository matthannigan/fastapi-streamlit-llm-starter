# Poetry Migration PRD

## Overview
Migrate the FastAPI-Streamlit LLM Starter project from traditional pip/requirements.txt dependency management to Poetry for improved dependency resolution, environment management, and development workflow consistency. This addresses recurring dependency conflicts (like the recent pytest 8.0 compatibility issue), production/development environment management challenges, and team collaboration consistency issues.

The current project suffers from:
- Dependency conflicts between testing and production packages
- Manual dependency resolution for complex version constraints
- Inconsistent environments across team members and deployment stages
- Difficulty managing shared library dependencies across project components
- No reliable way to ensure reproducible builds

Poetry will provide deterministic dependency resolution, better separation of production/development dependencies, and improved developer experience through modern Python packaging standards.

## Core Features

### 1. Deterministic Dependency Resolution
**What it does**: Poetry's dependency resolver automatically finds compatible versions of all dependencies and locks them in poetry.lock
**Why it's important**: Eliminates "works on my machine" issues and prevents runtime dependency conflicts like the pytest 8.0 issue
**How it works**: Declares high-level requirements in pyproject.toml, Poetry resolves and locks specific versions that work together

### 2. Environment Separation
**What it does**: Clean separation between production, development, and testing dependencies with group-based organization
**Why it's important**: Reduces production image size, prevents test dependencies from affecting production, enables targeted installs
**How it works**: Uses dependency groups (`[tool.poetry.group.dev.dependencies]`) to organize packages by purpose

### 3. Shared Library Management
**What it does**: Proper handling of local shared library dependencies with automatic resolution
**Why it's important**: Current `-e ../shared` approach is fragile and doesn't work well with Docker multi-stage builds
**How it works**: Poetry path dependencies with proper version resolution and build integration

### 4. Modern Python Packaging
**What it does**: Uses pyproject.toml standard and provides built-in build/publish capabilities
**Why it's important**: Future-proofs the project and enables better tooling integration (IDEs, CI/CD, etc.)
**How it works**: Single pyproject.toml file replaces requirements.txt, setup.py, and other config files

### 5. Virtual Environment Management
**What it does**: Automatic virtual environment creation and management per project
**Why it's important**: Isolates project dependencies, prevents system Python pollution, consistent environments
**How it works**: `poetry install` creates/activates venv automatically, `poetry run` executes commands in correct environment

## User Experience

### Developer Personas
1. **Lead Developer**: Needs reliable dependency management, easy onboarding for new team members
2. **New Team Member**: Wants simple setup process, consistent development environment
3. **DevOps Engineer**: Requires reproducible builds, efficient Docker images, clear production dependencies

### Key Developer Flows

#### 1. Initial Setup Flow
```bash
# Current (error-prone)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e ../shared

# With Poetry (reliable)
poetry install
```

#### 2. Adding Dependencies Flow
```bash
# Current (manual conflict resolution)
# Add to requirements.txt, hope it works, fix conflicts manually

# With Poetry (automatic resolution)
poetry add streamlit
poetry add --group dev pytest
# Poetry automatically resolves compatible versions
```

#### 3. Production Deployment Flow
```bash
# Current (includes dev dependencies)
pip install -r requirements.txt

# With Poetry (production-only)
poetry install --only=main
```

### UI/UX Considerations
- Command consistency across all environments
- Clear error messages when dependencies conflict
- Intuitive dependency group organization
- Seamless integration with existing Docker workflow

## Technical Architecture

### System Components
1. **pyproject.toml**: Central configuration file replacing requirements.txt files
2. **poetry.lock**: Lock file ensuring reproducible installs
3. **Poetry CLI**: Dependency management and environment commands
4. **Virtual Environments**: Isolated per-project Python environments

### Project Structure Changes
```
frontend/
├── pyproject.toml          # Replaces requirements.txt + requirements-dev.txt
├── poetry.lock            # New: locked dependency versions
└── ...

backend/
├── pyproject.toml          # Replaces requirements.txt + requirements-dev.txt
├── poetry.lock            # New: locked dependency versions
└── ...

shared/
├── pyproject.toml          # New: proper package configuration
├── poetry.lock            # New: locked dependency versions
└── ...
```

### Data Models
- **Dependency Groups**: main, dev, test, docs, security
- **Version Constraints**: Semantic versioning with Poetry's constraint syntax
- **Path Dependencies**: Local shared library references

### Docker Integration
```dockerfile
# Multi-stage build with Poetry
FROM python:3.11-slim as base
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false

# Production stage
FROM base as production
RUN poetry install --only=main

# Development stage  
FROM base as development
RUN poetry install --with=dev
```

### Infrastructure Requirements
- Poetry installation in CI/CD pipelines
- Updated Docker build processes
- Team Poetry installation and training

## Development Roadmap

### Phase 1: Foundation Setup (MVP)
**Scope**: Convert one component to Poetry, establish patterns
- Install Poetry on development machines
- Convert `main/frontend` to Poetry
- Create pyproject.toml with current dependencies
- Generate initial poetry.lock
- Update frontend Dockerfile for Poetry
- Verify functionality with existing tests
- Document conversion process

**Success Criteria**: Frontend builds and runs identically with Poetry

### Phase 2: Full Project Conversion
**Scope**: Extend Poetry to all components
- Convert `main/backend` to Poetry
- Convert `main/shared` to proper Poetry package
- Update shared library dependencies in frontend/backend
- Convert `security/auth-hardening` branch components
- Update all Dockerfiles and docker-compose files
- Update CI/CD pipeline scripts

**Success Criteria**: All components use Poetry, shared library works correctly

### Phase 3: Advanced Features
**Scope**: Leverage Poetry's advanced capabilities
- Implement dependency groups for different environments
- Add Poetry scripts for common tasks
- Set up automated dependency updates
- Configure Poetry for package publishing (if needed)
- Optimize Docker builds with Poetry caching
- Create development environment automation

**Success Criteria**: Improved developer experience, faster builds, automated workflows

### Phase 4: Team Optimization
**Scope**: Team processes and advanced workflows
- Team training on Poetry workflows
- Establish dependency update procedures
- Create troubleshooting documentation
- Implement pre-commit hooks for poetry.lock
- Set up automated security scanning for dependencies
- Optimize CI/CD performance with Poetry caching

**Success Criteria**: Team proficient with Poetry, automated dependency management

## Logical Dependency Chain

### Foundation First
1. **Poetry Installation & Training**: Team needs Poetry knowledge before conversion
2. **Shared Library Conversion**: Must be converted first as other components depend on it
3. **Frontend Conversion**: Convert simpler component first to establish patterns

### Visible Progress Path
1. **Single Component Success**: Prove Poetry works with existing functionality
2. **Cross-Component Integration**: Demonstrate shared library integration works
3. **Full Environment Parity**: Show dev/prod environments work identically
4. **Performance Improvements**: Demonstrate faster builds and better dependency resolution

### Atomic Feature Scoping
1. **Per-Component Conversion**: Each component can be converted independently
2. **Incremental Docker Updates**: Update Dockerfiles as components are converted
3. **Parallel Branch Conversion**: Security branch can be converted separately
4. **Gradual CI/CD Migration**: Update pipeline scripts incrementally

## Risks and Mitigations

### Technical Challenges
**Risk**: Poetry learning curve for team members
**Mitigation**: Create comprehensive documentation, provide hands-on training sessions, start with one component

**Risk**: Dependency resolution issues during migration
**Mitigation**: Convert components incrementally, maintain fallback requirements.txt files temporarily, thorough testing

**Risk**: Docker build performance regression
**Mitigation**: Implement Poetry caching strategies, benchmark build times, optimize multi-stage builds

**Risk**: CI/CD pipeline disruption
**Mitigation**: Update pipelines incrementally, maintain parallel pip-based pipelines during transition

### MVP and Development Pacing
**Risk**: Over-engineering the initial conversion
**Mitigation**: Start with basic Poetry usage, add advanced features in later phases, focus on functional parity first

**Risk**: Team productivity loss during transition
**Mitigation**: Phase rollout across components, provide clear migration guides, allow parallel workflows initially

### Resource Constraints
**Risk**: Time investment for conversion and training
**Mitigation**: Allocate dedicated time for migration, start with least critical component, document learnings

**Risk**: Potential compatibility issues with existing tooling
**Mitigation**: Test integration with IDEs, linters, and deployment tools early, have rollback plans

## Appendix

### Research Findings
- Poetry has become the de facto standard for modern Python projects
- Major Python projects (FastAPI, Pydantic, etc.) use Poetry
- Docker integration patterns are well-established
- Team productivity typically improves after initial learning period

### Technical Specifications
- Poetry version: 1.7+ (latest stable)
- Python version compatibility: Maintain current 3.11+ requirement
- Lock file format: poetry.lock (standardized, deterministic)
- Configuration format: pyproject.toml (PEP 518 standard)

### Migration Checklist
- [ ] Install Poetry on all development machines
- [ ] Convert shared library to Poetry package
- [ ] Convert frontend component
- [ ] Convert backend component
- [ ] Update Docker configurations
- [ ] Update CI/CD pipelines
- [ ] Create team documentation
- [ ] Conduct team training
- [ ] Remove old requirements.txt files
- [ ] Update project README

### Command Reference
```bash
# Essential Poetry commands for team
poetry install                 # Install dependencies
poetry add package             # Add new dependency
poetry add --group dev package # Add development dependency
poetry remove package          # Remove dependency
poetry update                  # Update dependencies
poetry run command             # Run command in poetry environment
poetry shell                   # Activate poetry shell
poetry check                   # Validate pyproject.toml
poetry lock                    # Update poetry.lock
``` 