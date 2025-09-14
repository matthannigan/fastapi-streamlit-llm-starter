# Poetry Migration Task Plan

## Context and Rationale

The FastAPI-Streamlit-LLM-Starter project currently uses traditional pip/requirements.txt dependency management with pip-tools for lock file generation. While functional, this approach suffers from recurring dependency conflicts (like the documented pytest 8.0 compatibility issue), complex Docker configuration with multiple requirements files, manual dependency resolution challenges, and fragile shared library integration using `-e ../shared` editable installs.

### Current Dependency Management Analysis
- **Backend Components**: Uses `requirements.txt` + `requirements-dev.txt` with pip-tools generated `.lock` files
- **Frontend Components**: Mirror backend pattern with separate Docker-specific `requirements.docker.txt` files
- **Shared Library**: Already modernized with proper `pyproject.toml` configuration and Python 3.12+ requirement
- **Build System**: Makefile-driven workflow with root-level `.venv` management and pip-tools for dependency locking
- **Docker Integration**: Complex multi-file approach with different dependency files for Docker vs. local development

### Identified Pain Points
- **Dependency Resolution**: Manual conflict resolution when pip-tools fails to find compatible versions
- **Environment Inconsistency**: Different setups between local development, Docker, and CI/CD environments
- **Shared Library Integration**: Fragile `-e file:../shared` approach breaks in Docker multi-stage builds
- **Development Workflow**: Multiple dependency files to maintain per component (4 files per component: requirements.txt, requirements-dev.txt, requirements.lock, requirements-dev.lock)
- **Testing Complexity**: Current baseline shows 60 documented test failures, some related to dependency management issues

### Poetry Migration Benefits
- **Deterministic Resolution**: Poetry's SAT solver automatically handles complex dependency relationships that currently require manual intervention
- **Virtual Environment Management**: Built-in virtual environment handling replaces current Makefile complexity
- **Simplified Docker**: Single `pyproject.toml` per component eliminates need for multiple Docker-specific requirement files
- **Path Dependency Handling**: Proper local dependency resolution for shared library replaces fragile editable installs
- **Development Experience**: Unified workflow across all components with consistent dependency management commands

### Integration with Existing Infrastructure
- **Makefile Compatibility**: Poetry commands can be wrapped in existing Makefile targets
- **CI/CD Integration**: GitHub Actions workflows can be updated to use Poetry for more reliable builds
- **Docker Optimization**: Multi-stage builds can leverage Poetry's export functionality for production optimization
- **Root-level Management**: Poetry can manage project-level dependencies while maintaining component-specific configurations

### Desired Outcome
A modernized dependency management system using Poetry across all components with deterministic dependency resolution, simplified Docker configuration, reliable shared library integration, and improved developer experience while maintaining compatibility with existing Makefile-driven workflow and infrastructure.

---

## Implementation Phases Overview

**Phase 1: Foundation Setup (2-3 days)**
Establish Poetry installation and convert the shared library to proper Poetry package. Create Poetry configurations for backend and frontend components while maintaining existing functionality.

**Phase 2: Workflow Integration (3-4 days)**  
Update Makefile targets, Docker configurations, and CI/CD pipelines to use Poetry. Validate that all existing development and deployment workflows continue to function.

**Phase 3: Advanced Features & Optimization (1-2 weeks)**
Leverage Poetry's advanced features for dependency groups, scripts, and optimized builds. Complete migration validation and team training.

---

## Phase 1: Foundation Setup

### Deliverable 1: Poetry Installation and Shared Library Migration
**Goal**: Install Poetry across development environments and properly migrate shared library to Poetry package structure.

#### Task 1.1: Poetry Installation and Environment Setup
- [ ] Install Poetry on all development machines using the official installer:
  - [ ] Download and run Poetry installer: `curl -sSL https://install.python-poetry.org | python3 -`
  - [ ] Add Poetry to PATH and verify installation: `poetry --version`
  - [ ] Configure Poetry to create virtual environments in project directory: `poetry config virtualenvs.in-project true`
  - [ ] Configure Poetry to use system keyring for credentials: `poetry config keyring.enabled true`
- [ ] Team training on Poetry basics:
  - [ ] Create team documentation with essential Poetry commands
  - [ ] Document Poetry configuration and workflow differences from current pip/pip-tools setup
  - [ ] Provide hands-on training session for team members
  - [ ] Establish team conventions for Poetry usage and commit practices

#### Task 1.2: Shared Library Poetry Package Conversion
- [ ] **CRITICAL PATH**: Convert `shared/` to proper Poetry package:
  - [ ] Backup existing `shared/pyproject.toml` configuration
  - [ ] Initialize Poetry in shared directory: `cd shared && poetry init`
  - [ ] Migrate existing pyproject.toml metadata to Poetry format:
    - [ ] Convert `[project]` section to `[tool.poetry]` format
    - [ ] Update version, description, and author information
    - [ ] Transform dependency specifications from PEP 621 to Poetry format
  - [ ] Configure shared library dependencies:
    - [ ] Migrate `dependencies = ["pydantic>=2.11.0"]` to Poetry format
    - [ ] Set up development dependencies group for testing
    - [ ] Maintain Python 3.12+ requirement: `python = "^3.12"`
- [ ] Validate shared library Poetry configuration:
  - [ ] Test `poetry install` in shared directory creates proper environment
  - [ ] Verify shared library can be imported and used correctly
  - [ ] Test `poetry build` produces proper wheel and source distributions
  - [ ] Confirm no regression in shared library functionality

#### Task 1.3: Backend Component Poetry Migration
- [ ] Initialize Poetry in backend directory:
  - [ ] Run `cd backend && poetry init --no-interaction`
  - [ ] Configure basic project metadata (name, version, description)
  - [ ] Set Python version requirement to `"^3.12"` for consistency
- [ ] Convert backend dependencies to Poetry format:
  - [ ] Migrate production dependencies from `requirements.txt`:
    - [ ] FastAPI: `poetry add "fastapi>=0.110.0"`
    - [ ] Uvicorn: `poetry add "uvicorn[standard]>=0.24.0,<0.25.0"`
    - [ ] Pydantic dependencies: `poetry add "pydantic>=2.10" "pydantic-settings>=2.0.0" "pydantic-ai>=0.2.8,<0.3.0"`
    - [ ] Infrastructure dependencies: `poetry add httpx requests redis tenacity circuitbreaker psutil brotli`
  - [ ] Set up dependency groups for backend:
    - [ ] Create dev group: `poetry add --group dev pytest pytest-asyncio pytest-cov pytest-xdist httpx requests`
    - [ ] Create testing group: `poetry add --group testing pytest-redis pytest-timeout pytest-retry pytest-random-order`
    - [ ] Create quality group: `poetry add --group quality flake8 mypy black isort pre-commit`
- [ ] Configure shared library as path dependency:
  - [ ] Add shared library dependency: `poetry add --path ../shared`
  - [ ] Test that shared library imports work correctly in backend context
  - [ ] Verify that Poetry resolves shared library dependencies properly

#### Task 1.4: Frontend Component Poetry Migration  
- [ ] Initialize Poetry in frontend directory:
  - [ ] Run `cd frontend && poetry init --no-interaction`
  - [ ] Configure project metadata consistent with backend
  - [ ] Set Python version requirement to `"^3.12"`
- [ ] Convert frontend dependencies to Poetry format:
  - [ ] Migrate core dependencies from `requirements.txt`:
    - [ ] Streamlit: `poetry add "streamlit>=1.28.1,<1.29.0"`
    - [ ] HTTP client: `poetry add "httpx>=0.28.1"`
    - [ ] Configuration: `poetry add "pydantic-settings>=2.0.3,<3.0.0" "python-dotenv>=1.0.0,<2.0.0"`
  - [ ] Set up frontend dependency groups:
    - [ ] Create dev group: `poetry add --group dev pytest pytest-asyncio pytest-cov pytest-xdist`
    - [ ] Create quality group: `poetry add --group quality flake8 black isort`
- [ ] Configure shared library path dependency:
  - [ ] Add shared library: `poetry add --path ../shared`
  - [ ] Verify frontend can import and use shared models correctly
  - [ ] Test that Poetry virtual environment works with Streamlit

---

### Deliverable 2: Basic Poetry Configuration Validation
**Goal**: Ensure Poetry configurations work correctly and maintain existing functionality.

#### Task 2.1: Dependency Resolution Validation
- [ ] Test Poetry dependency resolution across all components:
  - [ ] Run `poetry install` in shared/ directory and verify no conflicts
  - [ ] Run `poetry install` in backend/ directory with all groups
  - [ ] Run `poetry install` in frontend/ directory with all groups  
  - [ ] Verify that Poetry lock files (`poetry.lock`) are generated correctly
- [ ] Cross-component dependency compatibility:
  - [ ] Ensure shared library version constraints work across backend and frontend
  - [ ] Verify no conflicting dependency versions between components
  - [ ] Test that shared library changes trigger appropriate updates in dependent components
- [ ] Compare against current pip-tools setup:
  - [ ] Document any dependency version changes made by Poetry
  - [ ] Verify that Poetry resolves dependencies that were previously problematic
  - [ ] Confirm critical dependencies (FastAPI, Streamlit, Pydantic) remain at compatible versions

#### Task 2.2: Development Workflow Validation
- [ ] Test basic development workflows with Poetry:
  - [ ] Backend development: `cd backend && poetry install && poetry run uvicorn app.main:app --reload`
  - [ ] Frontend development: `cd frontend && poetry install && poetry run streamlit run app/app.py`
  - [ ] Shared library development: `cd shared && poetry install && poetry run python -c "from shared.models import *"`
- [ ] Test Poetry virtual environment management:
  - [ ] Verify `poetry shell` activates correct virtual environment for each component
  - [ ] Test `poetry run` executes commands in correct environment
  - [ ] Confirm Poetry virtual environments are isolated and don't conflict
- [ ] Testing workflow validation:
  - [ ] Backend testing: `cd backend && poetry run pytest`
  - [ ] Frontend testing: `cd frontend && poetry run pytest`
  - [ ] Verify test results match current baseline (compare against documented 60 test failures)

---

## Phase 2: Workflow Integration

### Deliverable 3: Makefile Integration and Docker Modernization
**Goal**: Update existing Makefile targets and Docker configurations to use Poetry while maintaining current development experience.

#### Task 3.1: Makefile Poetry Integration
- [ ] Update root-level Makefile to support Poetry:
  - [ ] Modify `venv` target to detect and use Poetry virtual environments
  - [ ] Update `install` target to use Poetry: `poetry install` instead of pip install
  - [ ] Create `poetry-install` target for explicit Poetry setup
  - [ ] Update `PYTHON_CMD` detection to work with Poetry virtual environments
- [ ] Update component-specific Makefile targets:
  - [ ] Modify `install-backend` to use: `cd backend && poetry install --with dev,testing,quality`
  - [ ] Update `install-frontend` to use: `cd frontend && poetry install --with dev,quality`
  - [ ] Update `test-backend` to use: `cd backend && poetry run pytest`
  - [ ] Update `test-frontend` to use: `cd frontend && poetry run pytest`
- [ ] Maintain backward compatibility:
  - [ ] Keep existing target names and behavior
  - [ ] Add Poetry-specific targets as alternatives
  - [ ] Provide clear error messages if Poetry is not installed
  - [ ] Document migration path for developers

#### Task 3.2: Docker Configuration Updates
- [ ] Update backend Dockerfile for Poetry:
  - [ ] Install Poetry in base Docker stage: `pip install poetry==1.7+`
  - [ ] Configure Poetry for Docker: `poetry config virtualenvs.create false`
  - [ ] Replace requirements.txt copying with: `COPY pyproject.toml poetry.lock ./`
  - [ ] Update dependency installation: `poetry install --only=main` for production
  - [ ] Update development stage: `poetry install --with dev` for development builds
- [ ] Update frontend Dockerfile for Poetry:
  - [ ] Mirror backend Poetry installation and configuration
  - [ ] Replace frontend requirements file copying with Poetry files
  - [ ] Update shared library installation to use Poetry path dependencies
  - [ ] Test frontend Docker build produces identical functionality
- [ ] Create optimized Docker workflows:
  - [ ] Implement Poetry export for production builds: `poetry export -f requirements.txt --without-hashes`
  - [ ] Create Docker-specific Poetry configuration for faster builds
  - [ ] Update docker-compose.yml to work with Poetry-based containers

#### Task 3.3: CI/CD Pipeline Updates
- [ ] Update GitHub Actions workflows for Poetry:
  - [ ] Install Poetry in CI environment: `pip install poetry`
  - [ ] Replace pip install steps with `poetry install` in test workflows
  - [ ] Update caching strategies to cache Poetry virtual environments and lock files
  - [ ] Modify test execution to use `poetry run` commands
- [ ] Update dependency management workflows:
  - [ ] Replace `make lock-deps` with Poetry lock file management
  - [ ] Update dependency update process to use `poetry update`
  - [ ] Configure automated Poetry lock file generation and committing
  - [ ] Set up Poetry dependency security scanning

---

### Deliverable 4: Advanced Docker Integration and Performance
**Goal**: Optimize Docker builds with Poetry and implement advanced Poetry features for production deployment.

#### Task 4.1: Docker Multi-stage Poetry Optimization
- [ ] Implement optimized Docker multi-stage builds:
  - [ ] Create dedicated Poetry installation stage
  - [ ] Separate dependency installation from application code copying
  - [ ] Use Poetry export for lightweight production images
  - [ ] Implement proper Poetry cache mounting for faster builds
- [ ] Backend Docker optimization:
  - [ ] Create production stage using `poetry export --only=main | pip install`
  - [ ] Development stage using full Poetry installation
  - [ ] Test stage using Poetry with test dependencies
  - [ ] Validate image size reduction and build time improvement
- [ ] Frontend Docker optimization:
  - [ ] Apply similar multi-stage approach for frontend
  - [ ] Handle shared library dependencies correctly in Docker context
  - [ ] Optimize for Streamlit-specific requirements
  - [ ] Validate frontend Docker functionality matches current behavior

#### Task 4.2: Poetry Scripts and Development Tools
- [ ] Configure Poetry scripts in pyproject.toml files:
  - [ ] Backend scripts: `dev = "uvicorn app.main:app --reload"`, `test = "pytest"`
  - [ ] Frontend scripts: `dev = "streamlit run app/app.py"`, `test = "pytest"`
  - [ ] Shared library scripts: `test = "pytest"`, `build = "python -m build"`
- [ ] Set up Poetry plugin integrations:
  - [ ] Install poetry-plugin-export for requirements.txt generation if needed
  - [ ] Configure poetry-plugin-up for dependency updates
  - [ ] Set up pre-commit hooks that work with Poetry
- [ ] Development environment automation:
  - [ ] Create Poetry-based setup scripts
  - [ ] Configure IDE integration (VS Code, PyCharm) with Poetry
  - [ ] Document Poetry workflow for team members

---

## Phase 3: Advanced Features & Optimization

### Deliverable 5: Production Deployment and Performance Optimization
**Goal**: Leverage Poetry's advanced features for production deployment optimization and implement comprehensive dependency management.

#### Task 5.1: Poetry Export and Production Builds
- [ ] Implement Poetry export strategy for production:
  - [ ] Configure `poetry export` for different environments (production, development, testing)
  - [ ] Create optimized requirements.txt files for Docker production builds
  - [ ] Test that exported requirements maintain same dependency versions as Poetry lock
  - [ ] Validate production deployments work identically with exported requirements
- [ ] Advanced dependency group management:
  - [ ] Refine dependency groups based on actual usage patterns
  - [ ] Create minimal production groups that exclude unnecessary dependencies
  - [ ] Set up optional dependency groups for different features
  - [ ] Document dependency group strategy for team
- [ ] Performance optimization:
  - [ ] Benchmark Poetry install vs. current pip-tools workflow
  - [ ] Optimize Docker layer caching with Poetry
  - [ ] Measure and document build time improvements
  - [ ] Validate memory usage and startup time in production

#### Task 5.2: Advanced Poetry Features Implementation  
- [ ] Implement Poetry dependency constraints and overrides:
  - [ ] Configure dependency constraints for security and compatibility
  - [ ] Set up dependency source priorities if using private repositories
  - [ ] Implement dependency lock strategies for reproducible builds
- [ ] Configure Poetry publishing (if applicable):
  - [ ] Set up Poetry build configuration for shared library
  - [ ] Configure publishing to private PyPI if needed
  - [ ] Set up automated versioning and release workflows
- [ ] Security and maintenance automation:
  - [ ] Set up Poetry audit for security scanning
  - [ ] Configure automated dependency updates with Poetry
  - [ ] Implement dependency vulnerability monitoring
  - [ ] Create automated Poetry lock file maintenance

---

### Deliverable 6: Migration Validation and Documentation
**Goal**: Comprehensive validation of Poetry migration success and creation of team documentation.

#### Task 6.1: Comprehensive System Testing
- [ ] **CRITICAL**: Compare against existing test baseline:
  - [ ] Run complete test suite with Poetry and compare against documented 60 test failures
  - [ ] Ensure NO NEW test failures introduced by Poetry migration
  - [ ] Document any improvement in existing test failures due to better dependency resolution
  - [ ] Validate that all infrastructure services (cache, resilience, monitoring, security) work identically
- [ ] End-to-end system validation:
  - [ ] Test complete development workflow from clone to running system
  - [ ] Validate Docker deployment pipeline works with Poetry
  - [ ] Test CI/CD pipeline produces identical results
  - [ ] Verify production deployment compatibility
- [ ] Performance validation:
  - [ ] Benchmark dependency installation times (Poetry vs. pip-tools)
  - [ ] Measure Docker build time improvements
  - [ ] Validate application startup times remain consistent
  - [ ] Document performance improvements achieved

#### Task 6.2: Team Migration and Training
- [ ] Create comprehensive Poetry migration documentation:
  - [ ] Update README.md with Poetry-based setup instructions
  - [ ] Create Poetry command reference for team
  - [ ] Document migration from pip-tools workflow
  - [ ] Provide troubleshooting guide for common Poetry issues
- [ ] Team training and knowledge transfer:
  - [ ] Conduct Poetry workflow training sessions
  - [ ] Create video documentation of new development workflow
  - [ ] Establish Poetry best practices for the team
  - [ ] Set up peer support system for Poetry adoption
- [ ] Legacy cleanup and finalization:
  - [ ] Remove old requirements.txt files after validation
  - [ ] Archive pip-tools configuration files
  - [ ] Update all documentation to reflect Poetry workflow
  - [ ] Create rollback procedures if needed

#### Task 6.3: Long-term Maintenance Setup
- [ ] Establish ongoing Poetry maintenance procedures:
  - [ ] Create Poetry update schedule and process
  - [ ] Set up automated dependency security scanning
  - [ ] Configure Poetry lock file maintenance workflows
  - [ ] Document Poetry version management strategy
- [ ] Advanced workflow optimization:
  - [ ] Set up Poetry workspace management for monorepo-style development
  - [ ] Configure cross-component dependency update procedures
  - [ ] Implement Poetry-based release management
  - [ ] Create advanced troubleshooting procedures
- [ ] Success criteria validation:
  - [ ] Confirm deterministic dependency resolution eliminates manual conflicts
  - [ ] Verify improved developer onboarding experience
  - [ ] Validate simplified Docker configuration
  - [ ] Document measurable improvements in dependency management

---

## Implementation Notes

### Phase Execution Strategy

**PHASE 1: Foundation Setup (2-3 Days) - IMMEDIATE START**
- **Deliverable 1**: Poetry installation, shared library conversion, component initialization
- **Deliverable 2**: Basic configuration validation and dependency resolution testing
- **Success Criteria**: All components have working Poetry configurations, existing functionality maintained

**PHASE 2: Workflow Integration (3-4 Days)**  
- **Deliverable 3**: Makefile updates, Docker modernization, CI/CD pipeline updates
- **Deliverable 4**: Advanced Docker optimization and Poetry scripts configuration
- **Success Criteria**: All existing workflows work with Poetry, Docker builds optimized, CI/CD functional

**PHASE 3: Advanced Features & Optimization (1-2 Weeks) - OPTIONAL ENHANCEMENTS**
- **Deliverable 5**: Production deployment optimization and advanced Poetry features
- **Deliverable 6**: Migration validation, documentation, and team training
- **Success Criteria**: Team fully trained on Poetry, documentation complete, measurable improvements documented

### Migration Strategy Principles
- **Incremental Migration**: Convert one component at a time, starting with shared library
- **Parallel Workflows**: Maintain existing pip-tools workflow during transition
- **Testing-First**: Validate each component works before proceeding to next
- **Rollback Ready**: Maintain ability to revert to pip-tools if critical issues arise
- **Team-Centered**: Prioritize developer experience and team adoption success

### Dependency Management Philosophy
- **Shared Library First**: Critical path component that other components depend on
- **Conservative Version Constraints**: Use compatible version ranges to minimize breaking changes
- **Group-Based Organization**: Logical separation of production, development, testing, and documentation dependencies
- **Path Dependency Handling**: Proper local development setup for shared library integration
- **Lock File Discipline**: Commit Poetry lock files to ensure reproducible builds across environments

### Integration with Existing Infrastructure
- **Makefile Compatibility**: Preserve existing developer workflow while adding Poetry benefits
- **Docker Optimization**: Leverage Poetry for better build caching and smaller production images  
- **CI/CD Enhancement**: Use Poetry's deterministic resolution for more reliable builds
- **Testing Baseline**: Maintain current test baseline (60 documented failures) as comparison point
- **Production Deployment**: Ensure zero-downtime migration with fallback procedures

### Success Metrics
- **Developer Experience**: Reduced setup time, fewer dependency conflicts, clearer error messages
- **Build Performance**: Faster Docker builds, more reliable CI/CD, optimized dependency installation
- **Maintenance Reduction**: Automated dependency updates, security scanning, simplified conflict resolution
- **Team Adoption**: Successful migration with no loss of productivity, positive developer feedback

### Risk Mitigation
- **Phased Approach**: Complete each phase before proceeding to minimize risk
- **Extensive Testing**: Validate functionality at each step using existing test suite
- **Documentation First**: Update documentation before implementing changes
- **Team Communication**: Regular check-ins and support during transition
- **Rollback Planning**: Maintain pip-tools configuration until Poetry fully validated