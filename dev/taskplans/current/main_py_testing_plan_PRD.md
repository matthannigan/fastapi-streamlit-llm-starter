# Overview
The `main.py` module serves as the primary entry point for our FastAPI application, implementing a sophisticated dual-API architecture with enterprise-grade features. This module is critical for system reliability, security, and maintainability as it orchestrates the entire application lifecycle, configuration management, and infrastructure integration.

The module's complexity demands a comprehensive testing strategy that balances behavior-driven unit testing with integration validation across critical seams. Our testing approach must ensure confidence in the application factory pattern, dual-API separation, lifecycle management, and security boundaries while maintaining maintainability and refactoring resilience.

# Core Features
## App Factory Pattern Implementation
- **What it does**: Creates fresh FastAPI instances with complete configuration isolation, enabling test isolation and multi-instance deployment scenarios while maintaining backward compatibility
- **Why it's important**: Solves critical test isolation issues caused by module-level singletons, ensures environment variable changes propagate correctly in tests, and supports both production singleton and test multi-instance patterns
- **How it works**: Factory functions (`create_app()`, `create_public_app()`, `create_internal_app()`) create completely independent FastAPI instances from provided settings or fresh environment-derived settings

## Dual-API Architecture Management
- **What it does**: Manages separate public (`/v1/`) and internal (`/internal/`) API applications with distinct responsibilities, authentication strategies, and security boundaries
- **Why it's important**: Provides security isolation between external user access and administrative operations, enables independent scaling, and allows different documentation access patterns
- **How it works**: Creates two separate FastAPI applications with distinct middleware, router configurations, and documentation policies, then mounts internal app at `/internal` path

## Application Lifecycle Orchestration
- **What it does**: Manages sophisticated startup and shutdown procedures including infrastructure initialization, health system setup, operational logging, and graceful resource cleanup
- **Why it's important**: Ensures reliable service initialization, proper resource management, clean shutdowns, and operational visibility for production deployment
- **How it works**: Async context manager (`lifespan()`) handles startup logging, service initialization, error handling, and coordinated shutdown procedures

## Custom Documentation Generation
- **What it does**: Generates enhanced Swagger UI with cross-API navigation, professional styling, and clean OpenAPI schemas with security-aware access control
- **Why it's important**: Provides professional developer experience, maintains security boundaries in production, and enables easy navigation between public and internal API documentation
- **How it works**: Custom HTML generation (`get_custom_swagger_ui_html()`) and schema cleaning (`custom_openapi_schema()`) create branded documentation with navigation features

## Security and Configuration Management
- **What it does**: Implements production security hardening, environment-aware configuration, and authentication boundary enforcement
- **Why it's important**: Ensures secure deployment patterns, prevents information leakage, and maintains proper access controls across environments
- **How it works**: Security-aware documentation access, production mode restrictions, and settings-driven configuration with preset support

# User Experience
## Developer Personas
- **Backend Engineers**: Need reliable test isolation, clear configuration patterns, and maintainable code structure
- **DevOps Engineers**: Require predictable deployment patterns, proper lifecycle management, and operational visibility
- **Security Engineers**: Need confidence in security boundaries, proper authentication, and production hardening

## Key User Flows
- **Development Workflow**: Fast feedback loops with isolated test fixtures and reliable environment configuration
- **Testing Workflow**: Deterministic tests with proper isolation, comprehensive contract validation, and integration confidence
- **Deployment Workflow**: Predictable application startup, proper resource management, and operational readiness

## Technical Considerations
- **Test Performance**: Target <50ms execution for unit tests, <200ms for integration tests
- **Maintainability**: Tests must survive refactoring and implementation changes
- **Coverage Requirements**: Infrastructure components >90%, domain examples >70%
- **Environment Safety**: Proper test isolation using monkeypatch for environment variables

<PRD>
# Technical Architecture
## System Components
### App Factory Layer
- **`create_app()`**: Main factory with dual-API architecture support
- **`create_public_app()`**: Public API factory with external-facing features
- **`create_internal_app()`**: Internal API factory with administrative capabilities
- **Helper Factories**: `create_public_app_with_settings()`, `create_internal_app_with_settings()`

### Configuration Management
- **Settings Integration**: Factory pattern with `create_settings()` for test isolation
- **Environment Handling**: Proper environment variable management with monkeypatch
- **Preset Support**: Resilience and cache preset integration
- **Validation**: Pydantic-based configuration validation and error handling

### Documentation System
- **Swagger UI Generation**: Custom HTML with cross-API navigation
- **OpenAPI Cleaning**: Schema optimization and validation error removal
- **Security Controls**: Production mode documentation restrictions
- **Branding**: Professional styling and responsive design

### Lifecycle Management
- **Startup Orchestration**: Service initialization and health setup
- **Runtime Management**: Application operation and monitoring
- **Shutdown Coordination**: Graceful resource cleanup and connection termination

## Data Models
### Settings Objects
- **Configuration Contract**: Complete application settings with validation
- **Environment Integration**: Dynamic configuration from environment variables
- **Preset Application**: Resilience and cache preset enforcement
- **Override Support**: Custom configuration injection for testing

### Application State
- **FastAPI Instances**: Public and internal application objects
- **Middleware Stack**: Security, monitoring, and performance middleware
- **Router Configuration**: API endpoint registration and organization
- **Documentation State**: OpenAPI schema generation and caching

## APIs and Integrations
### Internal Dependencies
- **Core Configuration**: Settings management and validation
- **Environment Detection**: Production vs development mode handling
- **Middleware Stack**: Enhanced middleware setup and configuration
- **Router Integration**: API endpoint registration and organization

### External Integrations
- **Health Infrastructure**: Health check system initialization
- **Monitoring Systems**: Metrics and performance tracking
- **Security Systems**: Authentication and authorization integration
- **Documentation Tools**: Swagger UI and OpenAPI generation

## Infrastructure Requirements
### Testing Infrastructure
- **Test Isolation**: Fresh application instances per test
- **Environment Management**: Proper monkeypatch usage for environment variables
- **Mock Strategy**: High-fidelity fakes for infrastructure, minimal mocking
- **Performance Targets**: Sub-50ms unit test execution

### Development Infrastructure
- **Configuration Validation**: Settings validation and preset enforcement
- **Documentation Generation**: Real-time OpenAPI and Swagger UI updates
- **Hot Reloading**: Development-friendly configuration changes
- **Error Handling**: Structured error responses and logging

# Development Roadmap
## MVP Requirements
### Phase 1: Core Factory Testing
- **App Factory Unit Tests**: Test factory functions create properly configured applications
- **Settings Integration Tests**: Verify factory behavior with custom settings objects
- **Configuration Validation**: Test settings validation and error handling
- **Basic Lifecycle Tests**: Validate startup/shutdown procedures

### Phase 2: Dual-API Architecture Testing
- **Public API Tests**: Verify public application configuration and endpoints
- **Internal API Tests**: Validate internal application setup and security controls
- **API Separation Tests**: Ensure proper isolation between public and internal APIs
- **Router Integration Tests**: Test endpoint registration and organization

### Phase 3: Documentation System Testing
- **Swagger UI Generation**: Test custom HTML generation and navigation
- **OpenAPI Schema Cleaning**: Validate schema optimization and cleaning
- **Security Controls**: Test production mode documentation restrictions
- **Cross-API Navigation**: Verify navigation between public and internal docs

## Future Enhancements
### Phase 4: Advanced Integration Testing
- **Middleware Stack Integration**: Test complete middleware pipeline
- **Health Infrastructure Integration**: Validate health system initialization
- **Authentication Integration**: Test API key authentication across APIs
- **Environment-Aware Testing**: Test behavior across different environments

### Phase 5: Performance and Reliability
- **Concurrent Instance Testing**: Test multiple application instances
- **Resource Management**: Validate resource cleanup and memory management
- **Error Recovery**: Test graceful degradation and error handling
- **Performance Validation**: Ensure performance targets are met

# Logical Dependency Chain
## Foundation First
1. **App Factory Unit Tests** - Core factory behavior must work before any integration testing
2. **Settings Management Tests** - Configuration handling is prerequisite for all other tests
3. **Basic Lifecycle Tests** - Startup/shutdown procedures needed before endpoint testing

## Building Towards Usable Application
4. **Public API Configuration Tests** - Get external-facing API working first for immediate value
5. **Documentation Generation Tests** - Enable developer access to API documentation
6. **Internal API Tests** - Add administrative capabilities for operations teams

## Integration and Hardening
7. **Security Boundary Tests** - Implement and validate security controls
8. **Middleware Integration Tests** - Ensure complete request pipeline works
9. **Environment-Aware Tests** - Validate behavior across deployment environments

## Advanced Features
10. **Performance and Reliability Tests** - Optimize for production deployment
11. **Error Handling Validation** - Ensure robust error recovery
12. **Resource Management Tests** - Validate long-running application behavior

# Risks and Mitigations
## Technical Challenges
### Risk: Test Isolation Complexity
- **Challenge**: Maintaining proper test isolation with complex application factory
- **Mitigation**: Use function-scoped fixtures, monkeypatch for environment variables, and fresh instances per test

### Risk: Configuration State Pollution
- **Challenge**: Environment variable changes affecting subsequent tests
- **Mitigation**: Mandatory use of monkeypatch.setenv() with comprehensive fixture patterns

### Risk: Mock Strategy Complexity
- **Challenge**: Balancing realistic testing with test performance
- **Mitigation**: Use high-fidelity fakes (fakeredis) for infrastructure, minimal mocking of internal components

## MVP Definition Challenges
### Risk: Overly Comprehensive Scope
- **Challenge**: Trying to test every possible configuration and behavior
- **Mitigation**: Focus on critical paths and high-value user journeys, apply 80/20 rule for test coverage

### Risk: Brittle Test Implementation
- **Challenge**: Tests breaking during refactoring due to implementation dependencies
- **Mitigation**: Strict adherence to behavior-driven testing, focus on documented contracts only

## Resource Constraints
### Risk: Slow Test Execution
- **Challenge**: Integration tests taking too long and slowing development
- **Mitigation**: Performance targets (<50ms unit, <200ms integration), parallel test execution, strategic mocking

### Risk: Complex Test Maintenance
- **Challenge**: Test suite becoming too complex to maintain
- **Mitigation**: Consistent patterns, comprehensive documentation, regular test refactoring

# Appendix
## Testing Standards Compliance
### Behavior-Driven Testing
- All tests must focus on documented contracts in docstrings
- No testing of internal implementation details or private methods
- Tests should survive complete implementation refactoring

### Environment Variable Testing
- **Mandatory**: Use monkeypatch.setenv() for all environment variable manipulation
- **Forbidden**: Direct os.environ[] modification in any test code
- **Pattern**: Set environment before app creation, automatic cleanup after test

### Mock Strategy Guidelines
- **External Dependencies**: Mock APIs, databases, third-party services
- **Internal Collaborators**: Keep real implementation to preserve component integrity
- **High-Fidelity Fakes**: Prefer fakeredis, test containers over simple mocks

## Critical Integration Points
### Configuration Management Seams
- Settings Factory ↔ App Factory integration
- Environment Variable Detection ↔ Configuration Application
- Preset System ↔ Individual Setting Overrides

### Dual-API Architecture Seams
- Public App ↔ Internal App separation
- Router Registration ↔ Middleware Application
- Documentation Access ↔ Security Controls

### Lifecycle Management Seams
- Startup Procedures ↔ Service Initialization
- Runtime Operation ↔ Health Monitoring
- Shutdown Coordination ↔ Resource Cleanup

## Success Criteria
### Coverage Targets
- **Infrastructure Components**: >90% test coverage
- **Domain Examples**: >70% test coverage
- **Critical Paths**: 100% behavior coverage
- **Configuration Management**: 100% contract coverage

### Performance Targets
- **Unit Tests**: <50ms execution time
- **Integration Tests**: <200ms execution time
- **Test Suite**: Complete execution <5 minutes
- **Parallel Execution**: Support for concurrent test running

### Quality Metrics
- **Test Reliability**: 100% deterministic execution
- **Maintainability**: Tests survive refactoring without changes
- **Documentation**: Comprehensive test documentation with business impact
- **Isolation**: Zero test state pollution between tests
</PRD>