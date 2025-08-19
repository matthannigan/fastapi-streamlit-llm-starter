# Phase 4 Task Plan: Cache Configuration Preset System

## Context and Rationale

The cache infrastructure has grown to 28+ environment variables (`CACHE_*` variables), creating the same complexity problem that the resilience system experienced with 47 environment variables. This complexity makes the template difficult to configure, maintain, and adopt. The resilience system successfully resolved this by implementing a preset-based approach with `RESILIENCE_PRESET`, reducing 47 variables to a single preset choice with optional overrides.

### Identified Issues
- **Configuration Complexity**: 28+ CACHE_* environment variables overwhelming users
- **Maintenance Burden**: Each new cache feature adds more environment variables
- **Docker Compose Clutter**: Environment sections becoming unwieldy
- **User Experience**: 30-minute configuration instead of 5-minute setup
- **Pattern Inconsistency**: Cache system doesn't follow resilience system's successful preset pattern

### Current Environment Variables (28+ total)
- **Connection Variables (4)**: `CACHE_REDIS_URL`, `REDIS_URL`, `AI_CACHE_REDIS_URL`, `TEST_REDIS_URL`
- **Core Settings (8)**: `CACHE_DEFAULT_TTL`, `CACHE_MEMORY_CACHE_SIZE`, `CACHE_COMPRESSION_THRESHOLD`, etc.
- **AI-Specific (3)**: `ENABLE_AI_CACHE`, `CACHE_OPERATION_TTLS`, `CACHE_TEXT_SIZE_TIERS`
- **Security (6)**: `CACHE_USE_TLS`, `CACHE_USERNAME`, `CACHE_PASSWORD`, certificate paths
- **Performance (4)**: `CACHE_MAX_CONNECTIONS`, timeouts, batch size
- **Monitoring (3)**: `CACHE_ENABLE_MONITORING`, `CACHE_LOG_LEVEL`, health check settings

### Refactoring Goals
- **Dramatic Simplification**: Reduce 28+ variables to 3-5 variables using presets
- **Pattern Consistency**: Match resilience system's successful preset approach
- **Better User Experience**: Enable 5-minute setup with sensible defaults
- **Maintain Flexibility**: Preserve ability to override essential settings
- **Backward Compatibility**: Ensure existing configurations continue working

### Desired Outcome
A preset-based cache configuration system where users choose `CACHE_PRESET=development` instead of configuring 28+ individual variables, following the successful pattern established by `RESILIENCE_PRESET`.

---

## Deliverable 1: Implement CACHE_PRESET Environment Variable Support
**Goal**: Add preset-based configuration loading to the cache dependencies system, following the proven resilience pattern architecture.

### Task 1.1: Create Core Preset Architecture (Mirror Resilience Pattern)
- [X] **Create `backend/app/infrastructure/cache/cache_presets.py`** (following `resilience/config_presets.py`)
  - [X] Implement `CacheStrategy` enum (equivalent to `ResilienceStrategy`)
  - [X] Create `CacheConfig` dataclass (equivalent to `ResilienceConfig`)
  - [X] Implement `CachePreset` class (equivalent to `ResiliencePreset`)
  - [X] Create `CachePresetManager` class (equivalent to `PresetManager`) with environment detection
  - [X] Add preset definitions: `disabled`, `simple`, `development`, `production`, `ai-development`, `ai-production`
  - [X] Implement `to_cache_config()` method for preset conversion
  - [X] Add environment detection and recommendation capabilities

### Task 1.2: Integrate with Application Configuration (Mirror Resilience Pattern)
- [X] **Update `backend/app/core/config.py`** (following resilience integration pattern)
  - [X] Add `cache_preset: str` field with default="development"
  - [X] Implement `validate_cache_preset()` field validator (mirror `validate_resilience_preset`)
  - [X] Add allowed preset validation with descriptive error messages
  - [X] Integrate cache preset loading in configuration initialization
  - [X] Add cache configuration context tracking for monitoring

### Task 1.3: Update Dependencies Configuration Loading 
- [X] **Modify `backend/app/infrastructure/cache/dependencies.py`**
  - [X] Add `CACHE_PRESET` environment variable support in `get_cache_config()`
  - [X] Mirror the resilience configuration loading pattern from `backend/app/dependencies.py`
  - [X] Replace auto-detection logic with explicit preset selection
  - [X] Implement preset-based configuration loading with fallback mechanisms
  - [X] Add comprehensive error handling and logging for preset selection

### Task 1.4: Implement Override System (Match Resilience Override Pattern)
- [X] **Add override support following resilience `RESILIENCE_CUSTOM_CONFIG` pattern:**
  - [X] Support for `CACHE_REDIS_URL` environment variable override
  - [X] Support for `ENABLE_AI_CACHE` feature toggle override  
  - [X] Support for `CACHE_CUSTOM_CONFIG` JSON-based advanced overrides
  - [X] Implement override precedence: Custom Config > Environment Variables > Preset Defaults
  - [X] Add JSON schema validation for custom configuration overrides
  - [X] Log all applied overrides with context for debugging

### Task 1.5: Create Configuration Validation System
- [X] **Create `backend/app/infrastructure/cache/cache_validator.py`** (following `resilience/config_validator.py`)
  - [X] Implement JSON schema definitions for cache configuration validation
  - [X] Add configuration templates for common use cases (fast_development, robust_production)
  - [X] Create validation utilities with comprehensive error reporting
  - [X] Add configuration comparison and recommendation functionality
  - [X] Implement validation caching and performance optimization

### Task 1.6: Add Integration with Existing EnvironmentPresets
- [X] **Update existing `EnvironmentPresets` class integration:**
  - [X] Map preset values to enhanced preset system:
    - [X] `development` → `CachePresetManager.get_preset("development")`
    - [X] `testing` → `CachePresetManager.get_preset("development")`  
    - [X] `production` → `CachePresetManager.get_preset("production")`
    - [X] `ai-development` → `CachePresetManager.get_preset("ai-development")`
    - [X] `ai-production` → `CachePresetManager.get_preset("ai-production")`
  - [X] Ensure backward compatibility with existing `EnvironmentPresets` methods
  - [X] Add migration path from current environment-based detection to preset system

---

## Deliverable 2: Update Docker Compose and Environment Templates
**Goal**: Simplify Docker Compose configurations and environment templates to use the new preset system, following the resilience Docker integration pattern.

### Task 2.1: Update Main Docker Compose Files (Follow Resilience Pattern)
- [X] **Update `docker-compose.yml` environment section** (following resilience compose pattern)
  - [X] Replace 10+ CACHE_* variables with `CACHE_PRESET=${CACHE_PRESET:-development}`
  - [X] Keep essential overrides: `CACHE_REDIS_URL`, `ENABLE_AI_CACHE`
  - [X] Remove redundant cache configuration variables
  - [X] Add comments explaining preset-based approach matching resilience format
- [X] **Update `docker-compose.dev.yml` for development** (mirror `RESILIENCE_PRESET=${RESILIENCE_PRESET:-development}`)
  - [X] Set `CACHE_PRESET=${CACHE_PRESET:-development}`
  - [X] Enable debug-friendly overrides: `CACHE_LOG_LEVEL=DEBUG`
  - [X] Keep monitoring enabled for development insights
  - [X] Match resilience environment variable structure and organization
- [X] **Update `docker-compose.prod.yml` for production**
  - [X] Set `CACHE_PRESET=${CACHE_PRESET:-production}`
  - [X] Add production-specific overrides for performance
  - [X] Follow resilience production configuration patterns

### Task 2.2: Create Management and Tooling Scripts (Match Resilience Tooling)
- [X] **Create `backend/scripts/validate_cache_config.py`** (following `validate_resilience_config.py`)
  - [X] Implement preset validation, listing, and recommendation utilities
  - [X] Add `--list-presets`, `--show-preset`, `--validate-current` options
  - [X] Add `--recommend-preset ENV` for environment-based recommendations
  - [X] Include quiet mode and detailed reporting options
- [X] **Create `backend/scripts/migrate_cache_config.py`** (following `migrate_resilience_config.py`)
  - [X] Legacy configuration analysis and migration recommendations
  - [X] Automatic migration from individual variables to preset system
  - [X] Backward compatibility validation and testing

### Task 2.3: Add Makefile Integration (Match Resilience Commands)
- [X] **Add cache preset management commands to `Makefile`** (following resilience command pattern)
  - [X] `list-cache-presets`: List available cache configuration presets
  - [X] `show-cache-preset PRESET=development`: Show preset details
  - [X] `validate-cache-config`: Validate current cache configuration
  - [X] `validate-cache-preset PRESET=simple`: Validate specific preset
  - [X] `recommend-cache-preset ENV=production`: Get preset recommendation
  - [X] `migrate-cache-config`: Legacy configuration migration utilities

### Task 2.4: Create Simplified Environment Templates
- [X] **Update `.env.cache.template` to be preset-focused**
  - [X] Lead with `CACHE_PRESET` selection matching resilience template format
  - [X] Show all available preset options with descriptions
  - [X] Minimize individual variables to essential overrides only
- [X] **Create `.env.cache.examples` with common scenarios**
  - [X] Simple web application setup
  - [X] AI-powered application setup  
  - [X] High-performance production setup
  - [X] Development with debugging setup
- [X] **Enhance `.env.cache.simple.template`** (already created) as primary template

### Task 2.5: Update Configuration Documentation
- [X] **Update `docs/guides/infrastructure/REDIS_ENVIRONMENT_VARIABLES.md`**
  - [X] Add preset-based configuration section
  - [X] Show before/after comparison (28 vars → 3 vars)
  - [X] Document override patterns and use cases
- [X] **Create `docs/guides/infrastructure/CACHE_PRESETS.md`** (following resilience documentation structure)
  - [X] Document each preset with detailed settings
  - [X] Explain when to use each preset
  - [X] Show override examples for common customizations
  - [X] Include troubleshooting guide

### Task 2.6: Update Environment Variable References  
- [X] Update all documentation references to use preset approach
- [X] Update examples in code comments and docstrings
- [X] Update README files to show simplified configuration
- [X] Update FastAPI integration examples to use presets

---

## Deliverable 3: Enhance EnvironmentPresets and Configuration
**Goal**: Improve and expand the preset system to provide comprehensive, optimized configurations for different use cases.

### Task 3.1: Enhance Existing Presets
- [X] Review and optimize `EnvironmentPresets.development()`
  - [X] Ensure debugging-friendly settings
  - [X] Balance performance with development needs
  - [X] Include monitoring and logging appropriate for development
- [X] Review and optimize `EnvironmentPresets.testing()`
  - [X] Fast execution with minimal overhead
  - [X] Reduced TTLs for quick test cycles
  - [X] Memory-efficient settings
- [X] Review and optimize `EnvironmentPresets.production()`
  - [X] High-performance settings
  - [X] Extended TTLs for efficiency
  - [X] Optimized compression and connection pooling
- [X] Implement `EnvironmentPresets.ai_development()` if not exists
  - [X] Combine development settings with AI features enabled
  - [X] AI-specific debugging and monitoring
- [X] Implement `EnvironmentPresets.ai_production()` if not exists
  - [X] Combine production settings with optimized AI configurations
  - [X] AI-specific performance tuning
- [X] Add `EnvironmentPresets.minimal()` for lightweight deployments
  - [X] Minimal memory usage and features
  - [X] Suitable for resource-constrained environments

### Task 3.2: Add Preset Metadata and Documentation
- [X] Add metadata to each preset method
  - [X] Description of intended use case
  - [X] Key configuration values and rationale
  - [X] Performance characteristics
  - [X] Resource requirements

### Task 3.3: Add Preset Documentation Methods
- [X] Implement `EnvironmentPresets.list_presets()` method
  - [X] Return list of available presets with descriptions
  - [X] Include metadata for each preset
- [X] Add `EnvironmentPresets.describe_preset(name)` method
  - [X] Return detailed configuration for a specific preset
  - [X] Show all settings that will be applied

### Task 3.4: Implement Preset Validation and Testing
- [X] Add preset configuration validation
  - [X] Ensure all presets generate valid configurations
  - [X] Test preset compatibility with current cache infrastructure
- [X] Create preset comparison functionality
  - [X] Show differences between presets
  - [X] Help users choose appropriate preset
- [X] Add preset performance benchmarking
  - [X] Measure impact of different preset configurations
  - [X] Document performance characteristics

### Task 3.5: Create Configuration Comparison Tools
- [X] Implement preset comparison utilities
  - [X] Show configuration differences between presets
  - [X] Help users understand preset implications
- [X] Add configuration validation tools
  - [X] Validate custom configurations against presets
  - [X] Identify potential issues or optimizations
- [X] Create configuration export/import
  - [X] Export current configuration to JSON
  - [X] Import and apply configuration from JSON

### Task 3.6: Create Makefile Integration
- [X] Add `make cache-config-validate` command
  - [X] Validate current cache configuration
  - [X] Check preset consistency
- [X] Add `make cache-config-compare` command
  - [X] Compare current config with available presets
  - [X] Show optimization opportunities

---

## Deliverable 4: Update Testing and Validation
**Goal**: Ensure the preset system works correctly and doesn't break existing functionality.

### Task 4.1: Create New Preset System Tests (~400 lines, 1-2 days)
- [X] **Create `backend/tests/infrastructure/cache/test_dependencies.py`** (NEW FILE)
  - [X] Test `get_cache_config()` with all preset values (`development`, `testing`, `production`, `ai-development`, `ai-production`)
  - [X] Test `CACHE_PRESET` environment variable validation and error handling
  - [X] Test preset + override combinations (`CACHE_REDIS_URL`, `ENABLE_AI_CACHE`, `CACHE_CUSTOM_CONFIG`)
  - [X] Test override precedence: Custom Config > Environment Variables > Preset Defaults
  - [X] Test invalid preset names with descriptive error messages
  - [X] Test fallback to 'development' preset when `CACHE_PRESET` not specified
  - [X] Test preset configuration validation after loading
- [X] **Create `backend/tests/infrastructure/cache/test_preset_system.py`** (NEW FILE)
  - [X] Test preset validation and error handling utilities
  - [X] Test preset comparison and recommendation functionality
  - [X] Test preset metadata and documentation features
  - [X] Test configuration export/import functionality

### Task 4.2: Update High-Impact Test Files (~1,421 lines, 2-3 days)
**Files requiring significant updates based on test analysis:**

- [ ] **Update `backend/tests/infrastructure/cache/test_factory.py`** (567 lines)
  - [ ] Add preset-based factory method tests for `for_web_app()`, `for_ai_app()`, `for_testing()`
  - [ ] Test factory creation with preset configurations vs individual parameters
  - [ ] Test preset + override parameter combinations in all factory methods
  - [ ] Test fallback behavior when preset loading fails
  - [ ] Add tests for `create_cache_from_config()` with preset-based configurations
  - [ ] Validate cache behavior equivalence with preset vs manual configuration

- [ ] **Update `backend/tests/infrastructure/cache/test_ai_config.py`** (854 lines)
  - [ ] Add preset integration tests to existing `from_env()` tests
  - [ ] Test environment variable precedence with preset system
  - [ ] Add preset scenarios to configuration validation tests
  - [ ] Test preset + AI config combinations and inheritance
  - [ ] Update existing environment variable tests to work alongside preset system

### Task 4.3: Update Medium-Impact Test Files (~6,659 lines, 1-2 days)
**Files requiring minor preset test scenario additions:**

- [ ] **Update `backend/tests/infrastructure/cache/test_ai_cache_integration.py`** (2,500 lines)
  - [ ] Replace 5 `monkeypatch.setenv` calls with preset-based environment setup
  - [ ] Add preset configuration scenarios to existing integration tests
  
- [ ] **Update `backend/tests/infrastructure/cache/test_ai_cache_migration.py`** (1,200 lines)
  - [ ] Add preset examples to migration scenarios
  - [ ] Test migration compatibility with preset-based configurations
  
- [ ] **Update `backend/tests/infrastructure/cache/test_cross_module_integration.py`** (209 lines)
  - [ ] Update 1 `REDIS_URL` reference to use preset approach
  - [ ] Add preset configuration to integrated cache system fixture
  
- [ ] **Update benchmark test files** (2,750 lines total)
  - [ ] `benchmarks/test_integration.py`: Add preset scenarios to config loading tests
  - [ ] `benchmarks/test_core.py`: Add preset support to environment detection
  - [ ] `benchmarks/test_config.py`: Add preset tests to configuration loading
  - [ ] `benchmarks/conftest.py`: Add preset fixtures for test setup

### Task 4.4: Preserve Low-Impact Test Files (17 files, ~6,000 lines)
**No changes required for these files as confirmed by analysis:**
- [ ] **Verify** that core cache functionality tests remain unchanged:
  - [ ] `test_base.py`, `test_memory.py`, `test_redis_generic.py`, `test_redis_ai.py`
  - [ ] `test_redis_ai_inheritance.py`, `test_redis_ai_monitoring.py`
  - [ ] `test_key_generator.py`, `test_parameter_mapping.py`, `test_security.py`
  - [ ] `test_monitoring.py`, `test_migration.py`, `test_compatibility.py`
  - [ ] All benchmark model and utility tests (`test_models.py`, `test_utils.py`, etc.)

### Task 4.5: Comprehensive Integration and Regression Testing
- [ ] **Performance Regression Testing**
  - [ ] Benchmark preset loading performance vs individual variable loading
  - [ ] Ensure configuration creation time remains under acceptable thresholds
  - [ ] Test memory usage impact of preset system (should be minimal)

- [ ] **End-to-End Integration Testing**
  - [ ] Test full application startup with each preset configuration
  - [ ] Test Docker Compose environments with new preset variables
  - [ ] Validate FastAPI dependency injection with preset-based configurations
  - [ ] Test all cache functionality works identically with preset vs manual config

### Task 4.6: Test Infrastructure Updates
- [ ] **Update test fixtures and utilities** (`conftest.py` files)
  - [ ] Add preset-based environment setup helpers
  - [ ] Create preset configuration fixtures for common test scenarios
  - [ ] Update test isolation to handle preset environment variables

- [ ] **Add test parameterization** for preset combinations
  - [ ] Parameterize tests to run with different presets where applicable
  - [ ] Test preset + override combinations systematically
  - [ ] Validate consistent behavior across all preset configurations

### **Realistic Effort Estimation Based on Analysis:**
- **New Test Files**: 8-12 hours (1-2 days)
- **High-Impact Updates**: 16-24 hours (2-3 days) 
- **Medium-Impact Updates**: 8-16 hours (1-2 days)
- **Integration Testing**: 4-8 hours (0.5-1 day)
- **Total Testing Effort**: 36-60 hours (4.5-7.5 days)

### **Risk Mitigation Strategies:**
1. **Incremental Approach**: Start with new test files, then update high-impact files
2. **Preserve Existing Logic**: Add preset scenarios alongside existing tests rather than rewriting
3. **Focused Scope**: 60% of tests require no changes, preserving existing functionality validation

---

## Deliverable 5: Documentation and Examples
**Goal**: Create comprehensive documentation and examples for the new preset-based configuration system.

### Task 5.1: Update Core Documentation
- [ ] Update `backend/app/infrastructure/cache/README.md`
  - [ ] Replace configuration examples with preset-based approach
  - [ ] Add preset selection guide
  - [ ] Document override patterns
- [ ] Update main project documentation
  - [ ] Update `CLAUDE.md` environment variable sections
  - [ ] Update Docker setup instructions
  - [ ] Add preset system explanation

### Task 5.2: Create Preset Guide Documentation
- [ ] Create `docs/guides/infrastructure/CACHE_PRESET_GUIDE.md`
  - [ ] Comprehensive preset selection guide
  - [ ] Detailed configuration for each preset
  - [ ] Use case scenarios and recommendations
  - [ ] Troubleshooting common issues
- [ ] Update `docs/guides/infrastructure/CACHE_USAGE.md`
  - [ ] Replace individual variable examples with presets
  - [ ] Show preset + override patterns
  - [ ] Add performance considerations

### Task 5.3: Update Examples and Integration Guides
- [ ] Update `backend/examples/cache/phase3_fastapi_integration.py`
  - [ ] Use preset-based configuration
  - [ ] Show override examples
  - [ ] Demonstrate different preset scenarios
- [ ] Create new example applications
  - [ ] Simple web app with `development` preset
  - [ ] AI app with `ai-production` preset
  - [ ] High-performance app with custom overrides
- [ ] Update Docker integration examples
  - [ ] Simplified Docker Compose configurations
  - [ ] Environment-specific preset usage

### Task 5.4: Create Quick Start Guide
- [ ] Create `docs/get-started/CACHE_QUICK_START.md`
  - [ ] 5-minute setup guide using presets
  - [ ] Common configuration patterns
  - [ ] Troubleshooting quick reference
- [ ] Update main README.md
  - [ ] Show simplified cache configuration
  - [ ] Highlight preset-based approach benefits
  - [ ] Include performance and maintainability improvements

---

## Deliverable 6: Legacy Environment Variable Cleanup
**Goal**: Systematically remove all traces of the old 28+ individual CACHE_* environment variables since there are no current users and no deprecation period is needed.

### Task 6.1: Code and Configuration Cleanup
- [ ] **Remove individual CACHE_* environment variables from all files:**
  - [ ] Search codebase for all CACHE_* variable references and remove/replace
  - [ ] Update `app/core/config.py` to remove individual cache field definitions
  - [ ] Clean up any hardcoded CACHE_* variable usage in application code
  - [ ] Remove individual cache environment variables from dependency injection
  - [ ] Update configuration loading to only support preset-based approach

### Task 6.2: Documentation and Example Cleanup  
- [ ] **Remove all references to individual CACHE_* variables from documentation:**
  - [ ] Clean up all .md files in `docs/` directory
  - [ ] Remove individual variable examples from all documentation
  - [ ] Update all configuration guides to only show preset approach
  - [ ] Clean up code comments and docstrings referencing old variables
  - [ ] Update README files to remove individual variable references

### Task 6.3: Environment Template Cleanup
- [ ] **Remove or update all environment templates:**
  - [ ] Delete `.env.cache.template` with 28+ variables (replace with preset version)
  - [ ] Clean up any remaining individual variable templates
  - [ ] Update all example environment files
  - [ ] Remove individual variables from all Docker compose environment sections
  - [ ] Clean up any deployment scripts or configuration files

### Task 6.4: Example and Integration Cleanup
- [ ] **Update all code examples and integration guides:**
  - [ ] Clean up all files in `backend/examples/cache/`
  - [ ] Update FastAPI integration examples
  - [ ] Remove individual variables from test fixtures where not needed for backward compatibility testing
  - [ ] Update benchmarking and monitoring examples
  - [ ] Clean up any scripts that reference individual CACHE_* variables

### Task 6.5: Docker and Deployment Cleanup
- [ ] **Ensure Docker and deployment files only use preset approach:**
  - [ ] Final cleanup of all docker-compose files
  - [ ] Remove individual variables from all deployment documentation
  - [ ] Update any CI/CD configuration to use preset approach
  - [ ] Clean up any infrastructure-as-code templates

### Task 6.6: Validation and Final Verification
- [ ] **Ensure complete removal of legacy approach:**
  - [ ] Run comprehensive search for any remaining CACHE_* individual variable usage
  - [ ] Verify that only `CACHE_PRESET`, `CACHE_REDIS_URL`, `ENABLE_AI_CACHE`, and `CACHE_CUSTOM_CONFIG` remain
  - [ ] Test that application works correctly with only preset-based configuration
  - [ ] Validate that no broken references or examples remain

---

## Implementation Notes

### Priority Order
1. **Deliverable 1** (CACHE_PRESET Support) - Core functionality enabling presets
2. **Deliverable 2** (Docker & Templates) - User-facing simplification
3. **Deliverable 3** (Enhanced Presets) - Improved preset quality and options
4. **Deliverable 4** (Testing) - Ensure quality and reliability
5. **Deliverable 5** (Documentation) - Enable adoption and understanding
6. **Deliverable 6** (Legacy Cleanup) - Complete removal of old 28+ variable system

### Backward Compatibility Not Required
- There are no current template users. Backward compatibility is not required.

### Risk Mitigation
- Comprehensive testing of preset configurations
- Performance regression monitoring

### Success Metrics
- [ ] Configuration complexity: 28+ variables → 1 primary variable (`CACHE_PRESET`) + 2-3 overrides
- [ ] User experience: 5-minute setup vs 30-minute configuration
- [ ] Preset options: Support for `disabled`, `development`, `production`, `ai-development`, `ai-production`
- [ ] Documentation: Complete preset guide with examples
- [ ] Performance: No regression in cache performance
- [ ] Legacy cleanup: Complete removal of old 28+ individual CACHE_* variables
- [ ] Maintainability: Easier to add new features without more environment variables

---

## Post-Implementation Tasks

### Validation
- [ ] Run full test suite including preset system tests
- [ ] Execute cache operations with all preset configurations
- [ ] Validate Docker Compose environments work correctly

### User Communication
- [ ] Update template documentation to highlight simplified configuration

### Future Enhancements
- [ ] Consider additional preset variants based on user feedback
- [ ] Add configuration optimization suggestions
- [ ] Implement configuration drift detection
- [ ] Add preset usage analytics for improvement insights

---

## Integration with Resilience Pattern

This task plan deliberately mirrors the successful resilience system refactoring that reduced 47 environment variables to a single preset-based approach:

### **Core Pattern Comparison**

| Aspect | Resilience System | Cache System (Proposed) |
|--------|-------------------|-------------------------|
| **Environment Variables** | 47 → 1 (`RESILIENCE_PRESET`) | 28+ → 1 (`CACHE_PRESET`) |
| **Preset Options** | `simple`, `development`, `production` | `development`, `testing`, `production`, `ai-development`, `ai-production` |
| **Override Support** | `RESILIENCE_CUSTOM_CONFIG` | `CACHE_CUSTOM_CONFIG` |
| **Essential Overrides** | Individual env vars supported | `CACHE_REDIS_URL`, `ENABLE_AI_CACHE` |
| **Configuration Integration** | `app/core/config.py` with validation | Same configuration file pattern |
| **Docker Simplification** | Clean environment sections | Clean environment sections |
| **Makefile Commands** | `validate-config`, `list-presets` | Same command pattern for cache |

### **Architectural Benefits**

This consistency provides:
- **Familiar Pattern**: Users already understand resilience presets (`RESILIENCE_PRESET=development`)
- **Reduced Learning Curve**: Same approach for cache configuration (`CACHE_PRESET=development`)
- **Architectural Consistency**: Template follows consistent patterns across infrastructure services
- **Maintainability**: Both systems use the same successful approach
- **User Experience**: Single environment variable vs 28+ individual variables

### **Reference Implementation Files**

**Core Preset System Architecture:**
- **`backend/app/infrastructure/resilience/config_presets.py`**: Comprehensive preset management system with `ResilienceStrategy`, `ResilienceConfig`, `ResiliencePreset` classes, and `PresetManager` with environment detection
- **`backend/app/infrastructure/resilience/config_validator.py`**: JSON Schema validation, configuration templates, and validation utilities for custom overrides
- **`backend/app/core/config.py`**: Integration of preset system into main application settings with `resilience_preset` field and validation

**Dependencies and Integration:**
- **`backend/app/dependencies.py`**: Resilience configuration loading through preset system in application startup
- **`backend/app/infrastructure/resilience/README.md`**: Comprehensive documentation of preset system architecture

**Docker and Environment Integration:**
- **`docker-compose.dev.yml`**: Uses `RESILIENCE_PRESET=${RESILIENCE_PRESET:-development}` pattern
- **`docker-compose.prod.yml`**: Production preset configuration examples

**Management and Tooling:**
- **`backend/scripts/validate_resilience_config.py`**: Preset validation, listing, and recommendation utilities
- **`backend/scripts/migrate_resilience_config.py`**: Legacy configuration migration tools
- **`Makefile`**: Commands like `list-presets`, `validate-config`, `recommend-preset ENV=production`

**Testing Architecture:**
- **`backend/tests/infrastructure/resilience/`**: Comprehensive test suite for preset system validation

### **Cache System Implementation Strategy**

The cache preset system should follow this exact pattern:

1. **Core Classes** (mirror resilience pattern):
   - `CacheStrategy` → equivalent to `ResilienceStrategy`
   - `CacheConfig` → equivalent to `ResilienceConfig` 
   - `CachePreset` → equivalent to `ResiliencePreset`
   - `CachePresetManager` → equivalent to `PresetManager`

2. **Configuration Integration**:
   - Add `cache_preset: str` field to `app/core/config.py`
   - Add validation similar to `validate_resilience_preset`
   - Integrate with existing cache configuration loading

3. **Dependencies Integration**:
   - Update `backend/app/infrastructure/cache/dependencies.py` to load presets
   - Mirror the resilience configuration loading pattern in `get_cache_config()`

4. **Tooling and Management**:
   - Create `scripts/validate_cache_config.py` following resilience script patterns
   - Add Makefile commands: `list-cache-presets`, `validate-cache-config`, `recommend-cache-preset`

5. **Docker Integration**:
   - Use `CACHE_PRESET=${CACHE_PRESET:-development}` pattern in compose files
   - Follow same environment variable simplification approach

### **Proven Success Metrics**

The resilience system transformation achieved:
- **Configuration Complexity**: 47 variables → 1 variable (`RESILIENCE_PRESET`)
- **User Onboarding**: 30-minute configuration → 5-minute setup
- **Maintenance**: Easier to add features without environment variable proliferation
- **Adoption**: Simplified preset-based approach improved template usability

The cache system should achieve similar metrics:
- **Configuration Complexity**: 28+ variables → 1 variable (`CACHE_PRESET`)
- **Consistency**: Same preset approach across all infrastructure services
- **User Experience**: Familiar pattern from resilience system