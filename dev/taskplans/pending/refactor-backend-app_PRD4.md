# Backend Directory Refactoring PRD - Balanced Synthesis Approach

# Overview

The backend application has evolved organically, resulting in oversized files (up to 49KB), mixed concerns, and unclear separation between reusable infrastructure and domain-specific logic. This refactoring will restructure the FastAPI application using a balanced synthesis approach that emphasizes the distinction between Infrastructure Services (template value) and Domain Services (user customization points).

**Problem Statement:**
- Monolithic files violating Single Responsibility Principle
- Unclear distinction between reusable template components and example code
- Difficult navigation and maintenance due to mixed concerns
- No clear guidance for developers on where to add their business logic

**Target Audience:**
- Developers using this as a FastAPI LLM starter template
- Future maintainers of the template infrastructure
- Teams building applications on top of this template

**Value Proposition:**
- Clear separation between template infrastructure and customizable domain logic
- Improved maintainability through focused, single-purpose files
- Better onboarding experience with obvious customization points
- Scalable architecture that grows gracefully with project complexity

# Core Features

## 1. Infrastructure Services Elevation
**What it does:** Moves reusable, business-agnostic services to a top-level `infrastructure/` directory
**Why it's important:** Makes the template's core value immediately visible and protects it from accidental modification
**How it works:** 
- Cache, resilience, AI, security, and monitoring services become first-class citizens
- Each infrastructure service has a clear interface and implementation
- Services are designed to be business-agnostic and highly reusable

## 2. Domain Services Isolation
**What it does:** Creates a dedicated `services/` directory for business-specific logic with clear "replace me" indicators
**Why it's important:** Provides obvious customization points for developers building on the template
**How it works:**
- Text processing service serves as an example implementation
- Clear documentation indicates this is meant to be replaced
- Shows patterns for using infrastructure services

## 3. Balanced API Organization
**What it does:** Separates versioned public APIs from unversioned internal APIs
**Why it's important:** Maintains proper API versioning while keeping operational endpoints flexible
**How it works:**
- `api/v1/` contains versioned public endpoints
- `api/internal/` contains unversioned monitoring and admin endpoints
- Clear separation prevents versioning confusion

## 4. Simplified Core Configuration
**What it does:** Consolidates application setup and configuration into a focused `core/` directory
**Why it's important:** Distinguishes application-specific setup from reusable infrastructure
**How it works:**
- Single `config.py` for all settings (with clear sections)
- Centralized exception handling
- Application-wide middleware configuration

## 5. Example Implementations
**What it does:** Provides reference implementations in a dedicated `examples/` directory
**Why it's important:** Shows advanced patterns without cluttering production code
**How it works:**
- Complex usage examples moved out of main codebase
- Clear README indicating these are learning materials
- Demonstrates best practices for using infrastructure services

# User Experience

## Developer Journey

### 1. **Template User (Primary Persona)**
**Goal:** Build a new LLM-powered application quickly
**Journey:**
1. Clones template and explores structure
2. Immediately sees `infrastructure/` contains the valuable components
3. Recognizes `services/` contains replaceable example code
4. Replaces text processing with their own domain logic
5. Leverages infrastructure services through dependency injection

### 2. **Template Maintainer**
**Goal:** Improve and extend infrastructure services
**Journey:**
1. Works primarily in `infrastructure/` directory
2. Follows strict backward compatibility requirements
3. Updates examples to demonstrate new features
4. Ensures all changes maintain business-agnostic nature

### 3. **New Team Member**
**Goal:** Understand and contribute to existing project
**Journey:**
1. Clear directory structure guides exploration
2. Infrastructure vs Domain separation immediately apparent
3. Examples directory provides learning resources
4. Can contribute to domain logic without touching infrastructure

## Key Developer Flows

### Adding New Business Logic
1. Create new service in `services/` directory
2. Import required infrastructure services
3. Implement business logic using infrastructure capabilities
4. Create API endpoints in `api/v1/routers/`
5. Define schemas in `schemas/` directory

### Extending Infrastructure
1. Identify business-agnostic pattern
2. Create interface in infrastructure service
3. Implement with high test coverage
4. Update examples to demonstrate usage
5. Document stability guarantees

# Technical Architecture

## Proposed Directory Structure

```
backend/app/
├── main.py                          # FastAPI app setup, middleware, router registration
├── dependencies.py                  # Global dependency injection providers
├── __init__.py
│
├── api/                            # API Layer - All HTTP endpoints
│   ├── __init__.py
│   ├── v1/                         # Versioned public APIs
│   │   ├── __init__.py
│   │   ├── routers/                # Route handlers
│   │   │   ├── __init__.py
│   │   │   ├── text_processing.py  # /v1/process, /v1/batch_process
│   │   │   └── health.py           # /v1/health, /v1/auth/status
│   │   └── deps.py                 # API-specific dependencies (auth, rate limiting)
│   │
│   └── internal/                   # Unversioned internal APIs
│       ├── __init__.py
│       ├── monitoring.py           # /monitoring/* endpoints
│       └── admin.py                # /admin/*, /cache/* endpoints
│
├── core/                           # Application setup and configuration
│   ├── __init__.py
│   ├── config.py                   # All settings (organized by section)
│   ├── exceptions.py               # Custom exception hierarchy
│   └── middleware.py               # CORS, error handling, logging middleware
│
├── infrastructure/                 # Reusable technical services (TEMPLATE VALUE)
│   ├── __init__.py
│   ├── ai/                         # AI provider abstractions
│   │   ├── __init__.py
│   │   ├── client.py               # Abstract AI client interface
│   │   ├── gemini.py               # Google Gemini implementation
│   │   └── prompt_builder.py       # Prompt construction utilities
│   │
│   ├── cache/                      # Caching infrastructure
│   │   ├── __init__.py
│   │   ├── base.py                 # Cache interface (ABC)
│   │   ├── redis.py                # Redis cache implementation
│   │   └── memory.py               # In-memory cache implementation
│   │
│   ├── resilience/                 # Fault tolerance patterns
│   │   ├── __init__.py
│   │   ├── circuit_breaker.py      # Circuit breaker implementation
│   │   ├── retry.py                # Retry logic with strategies
│   │   └── presets.py              # Resilience configuration presets
│   │
│   ├── security/                   # Security utilities
│   │   ├── __init__.py
│   │   ├── auth.py                 # API key validation
│   │   ├── response_validator.py   # Response security validation
│   │   └── sanitization.py         # Input sanitization utilities
│   │
│   └── monitoring/                 # Observability infrastructure
│       ├── __init__.py
│       ├── metrics.py              # Performance metrics collection
│       ├── health.py               # Health check utilities
│       └── cache_monitor.py        # Cache performance monitoring
│
├── services/                       # Domain-specific business logic (REPLACE THIS)
│   ├── __init__.py
│   └── text_processing.py          # Example domain service
│
├── schemas/                        # Pydantic models for validation
│   ├── __init__.py
│   ├── text_processing.py          # Text processing request/response models
│   ├── monitoring.py               # Monitoring endpoint models
│   ├── resilience.py               # Resilience configuration models
│   └── common.py                   # Shared models and enums
│
└── examples/                       # Reference implementations (NOT FOR PRODUCTION)
    ├── __init__.py
    ├── README.md                   # "These are examples for learning!"
    └── advanced_text_processing.py # Complex usage patterns
```

## Design Principles

1. **Infrastructure vs Domain Separation**: Top-level distinction between reusable components and business logic
2. **Interface Segregation**: Clear interfaces in infrastructure allow for multiple implementations
3. **Dependency Inversion**: Domain services depend on infrastructure abstractions, not concrete implementations
4. **Single Responsibility**: Each file has one clear purpose
5. **Open/Closed**: Infrastructure open for extension, closed for modification

## Key Architectural Decisions

### API Versioning Strategy
- Public APIs under `v1/` maintain backward compatibility
- Internal APIs under `internal/` can evolve with deployments
- Clear separation prevents confusion about stability guarantees

### Configuration Consolidation
- Single `config.py` with sections instead of multiple files
- Environment-specific settings handled through environment variables
- Validation happens at startup

### Service Interfaces
- Infrastructure services provide abstract base classes
- Concrete implementations can be swapped via dependency injection
- Domain services compose infrastructure services

# Development Roadmap

## Phase 1: Foundation and Structure Setup
**Scope:** Create directory structure and establish patterns
- Create new directory structure with __init__.py files
- Set up `infrastructure/` and `services/` directories
- Create `examples/` directory with migration README
- Establish import patterns for gradual migration
- **Note:** Preserve existing function/class names for test compatibility

## Phase 2: Infrastructure Services Extraction
**Scope:** Move reusable services to infrastructure layer
- Extract cache service to `infrastructure/cache/`
  - Create `base.py` with cache interface
  - Move `AIResponseCache` to `redis.py` (keep class name)
  - Create `memory.py` for in-memory alternative
- Extract resilience services to `infrastructure/resilience/`
  - Move circuit breaker and retry logic (preserve class names)
  - Extract presets to separate file
- Extract security utilities to `infrastructure/security/`
  - Move auth, sanitization, and validation (keep function names)
- Extract monitoring to `infrastructure/monitoring/`
  - Move metrics and health check logic

## Phase 3: Core Configuration Consolidation
**Scope:** Simplify configuration and application setup
- Consolidate configuration into `core/config.py`
  - Merge all settings with clear section comments
  - Preserve `Settings` class name and structure
- Extract custom exceptions to `core/exceptions.py`
- Create `core/middleware.py` for application middleware

## Phase 4: API Layer Reorganization
**Scope:** Implement versioned/unversioned API separation
- Create `api/v1/routers/` directory
  - Move text processing endpoints to `text_processing.py`
  - Move health endpoints to `health.py`
- Create `api/internal/` directory
  - Move monitoring router (unversioned)
  - Move admin/resilience endpoints (unversioned)
- Update `api/v1/deps.py` with API dependencies
- Update main.py router registration

## Phase 5: Domain Services Simplification
**Scope:** Consolidate domain logic and create examples
- Consolidate text processing into single `services/text_processing.py`
  - Preserve `TextProcessorService` class name
  - Show infrastructure service usage patterns
- Move complex examples to `examples/` directory
- Add clear documentation about replaceability

## Phase 6: Schema Organization
**Scope:** Organize Pydantic models by feature
- Create feature-based schema files
  - `schemas/text_processing.py` (requests and responses)
  - `schemas/monitoring.py` (monitoring models)
  - `schemas/resilience.py` (configuration models)
  - `schemas/common.py` (shared enums and base models)
- Preserve all model class names for compatibility

## Phase 7: Integration and Cleanup
**Scope:** Update imports and validate functionality
- Update all import statements throughout codebase
- Ensure all endpoints continue to function
- Update dependencies.py with new paths
- Remove old empty directories
- Validate with existing tests (no test refactoring)
- Update documentation

# Logical Dependency Chain

## Foundation First (Phase 1)
**Dependencies:** None
**Enables:** All subsequent phases
**Critical:** Must establish structure before moving files

## Infrastructure Before Domain (Phase 2)
**Dependencies:** Phase 1 complete
**Enables:** Domain services to use infrastructure
**Critical:** Infrastructure must be stable before domain services reference it

## Configuration Before API (Phase 3)
**Dependencies:** Phase 1 complete
**Enables:** API layer to use consolidated configuration
**Parallelizable:** Can run alongside Phase 2

## API Reorganization (Phase 4)
**Dependencies:** Phases 1, 3 complete
**Enables:** Clear endpoint organization
**Note:** Must maintain all existing routes

## Domain and Schema Updates (Phases 5-6)
**Dependencies:** Phases 2, 4 complete
**Enables:** Clean domain implementation
**Parallelizable:** Can be done together

## Final Integration (Phase 7)
**Dependencies:** All previous phases
**Critical:** Validates entire refactoring

## Getting to Usable State Quickly
1. Phase 1 creates structure (no functionality change)
2. Phase 2 immediately provides reusable infrastructure
3. Phase 4 gives clean API organization
4. Each phase maintains working application

# Risks and Mitigations

## Technical Challenges

### Risk: Import Circular Dependencies
**Mitigation:**
- Create dependency graph before moving files
- Use TYPE_CHECKING imports where necessary
- Test imports after each file move
- Maintain careful separation between layers

### Risk: Breaking Existing Tests
**Mitigation:**
- Preserve all class and function names
- Keep method signatures identical
- Document any unavoidable changes
- Run test suite after each phase
- **Explicitly excluded:** Test refactoring is out of scope

### Risk: Configuration Migration Complexity
**Mitigation:**
- Keep configuration structure identical
- Only consolidate location, not format
- Extensive testing of configuration loading
- Maintain environment variable compatibility

## MVP Definition

### Minimum Viable Refactor
Successfully separate infrastructure from domain services while maintaining all existing functionality.

**Success Criteria:**
- All existing tests pass without modification
- Clear infrastructure vs domain separation
- Improved file organization (no file >500 lines)
- Documentation clearly indicates customization points

### What's Explicitly Excluded
- **Test Refactoring**: Tests remain in current structure
- **New Features**: No new functionality added
- **Performance Optimization**: Focus on structure, not speed
- **Breaking Changes**: All APIs remain compatible

## Resource Constraints

### Risk: Development Time Extension
**Mitigation:**
- Each phase is independently valuable
- Can pause after any phase
- Parallel work possible on some phases
- Clear success criteria for each phase

### Risk: Team Coordination
**Mitigation:**
- Feature branch strategy with frequent rebases
- Clear ownership of each phase
- Daily progress updates
- Pair programming for complex migrations

# Appendix

## Current File Analysis

### Oversized Files Requiring Split
- `config.py`: 37KB → Split into sections within `core/config.py`
- `resilience_endpoints.py`: 46KB → Split between `api/internal/admin.py` and `infrastructure/resilience/`
- `validation_schemas.py`: 49KB → Split between `schemas/` and `infrastructure/resilience/`

### File Migration Mapping

| Current Location | New Location | Notes |
|-----------------|--------------|-------|
| `app/config.py` | `app/core/config.py` | Consolidate all settings |
| `app/services/cache.py` | `app/infrastructure/cache/redis.py` | Preserve AIResponseCache name |
| `app/services/resilience.py` | `app/infrastructure/resilience/` | Split into multiple files |
| `app/services/text_processor.py` | `app/services/text_processing.py` | Simplify as example |
| `app/routers/monitoring.py` | `app/api/internal/monitoring.py` | Unversioned internal API |
| `app/auth.py` | `app/infrastructure/security/auth.py` | Preserve function names |

## Infrastructure vs Domain Guidelines

### Infrastructure Services (Keep These)
- Must be business-agnostic
- High test coverage (>90%)
- Stable API with backward compatibility
- Configuration-driven behavior
- Clear interfaces with multiple implementations

### Domain Services (Replace These)
- Business-specific logic
- Example implementations
- Lower test coverage acceptable (>70%)
- Expected to be modified/replaced
- Clear documentation of replaceability

## Success Metrics

### Quantitative
- No file exceeds 500 lines
- Maximum import depth of 3 levels
- All existing tests pass
- Zero breaking changes to public APIs

### Qualitative
- Clear infrastructure vs domain separation
- Obvious customization points
- Improved developer onboarding
- Better code organization

## Migration Tools

The scripts include comprehensive error handling, progress reporting, and actionable feedback to guide the refactoring process.

Both scripts are designed to be run during and after the refactoring process:
- Use `import_update_script.py` during each phase to update imports
- Use `structure_validation.py` after each phase to ensure architectural integrity

### 1. `import_update_script.py` - Automated Import Migration Tool

This script handles the automatic updating of import statements throughout the codebase:

**Features:**
- Comprehensive import mapping from old to new structure
- Handles both absolute and relative imports
- Dry-run mode to preview changes before applying
- Validates imports after updating to catch broken references
- Provides detailed summary of changes and errors
- Excludes virtual environments and cache directories

**Usage:**
```bash
# Preview changes without modifying files
cd backend && python scripts/import_update_script.py --dry-run --verbose

# Apply changes
cd backend && python scripts/import_update_script.py

# Run from a specific directory
cd backend && python scripts/import_update_script.py --root-dir /path/to/project
```

### 2. `structure_validation.py` - Project Structure Validation Tool

This script validates the refactored structure to ensure architectural principles are maintained:

**Features:**
- Detects circular dependencies between modules
- Validates layer hierarchy (e.g., API → Services → Infrastructure)
- Checks file size limits (default 500 lines)
- Tracks infrastructure vs domain module separation
- Measures import depth and complexity metrics
- Warns about domain services importing from each other
- Generates detailed JSON report with `--verbose` flag

**Usage:**
```bash
# Run validation with default settings
cd backend && python scripts/structure_validation.py

# Custom file size limit and detailed report
cd backend && python scripts/structure_validation.py --max-file-lines 300 --verbose

# Run from specific directory
cd backend && python scripts/structure_validation.py --root-dir /path/to/project
```

## Post-Refactoring Enhancements (Future)

1. **Test Restructuring**: Separate PRD for test organization
2. **Performance Optimization**: Profile and optimize critical paths
3. **Additional Infrastructure**: Rate limiting, database patterns
4. **Documentation Generation**: Auto-generate from structure