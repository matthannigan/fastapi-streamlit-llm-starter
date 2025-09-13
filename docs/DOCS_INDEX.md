# Documentation Index

## 📝 Template Documentation

- **[README About the Template](./README.md)**: Main project overview and quick start guide for the FastAPI-Streamlit-LLM starter template *(Last updated 2024-07-27)*

### Get Started

- **[Setup & Complete Systems Integration Guide](./get-started/SETUP_INTEGRATION.md)**: Ties together all components and provides complete usage examples to get up and running quickly *(Last updated 2025-07-31)*
- **[Checklist](./get-started/CHECKLIST.md)**: Complete installation and setup checklist covering initial setup, API keys, Docker configuration, testing, and development workflows *(Last updated 2025-07-31)*

### Template Explainer

- **[Dual API Architecture](./reference/key-concepts/DUAL_API_ARCHITECTURE.md)**: Sophisticated dual-API architecture that separates external business operations from internal infrastructure management with clear boundaries *(Last updated 2025-07-30)*
- **[Infrastructure vs Domain Services](./reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)**: Architectural distinction between reusable template components and application-specific business logic for maintaining template reusability *(Last updated 2025-07-30)*
- **Infrastructure Services**:
  - **[AI](./guides/infrastructure/AI.md)**: Production-ready, security-first AI infrastructure service with comprehensive protection against prompt injection attacks and flexible templating *(Last updated 2025-07-30)*
  - **Cache Infrastructure**: Comprehensive cache infrastructure with multi-tiered architecture, AI optimization, and production-ready patterns
    - **[Cache Overview](./guides/infrastructure/cache/CACHE.md)**: Cache infrastructure architecture, key features, and navigation hub *(Last updated 2025-08-27)*
    - **[Usage Guide](./guides/infrastructure/cache/usage-guide.md)**: Practical implementation patterns, factory methods, and developer productivity *(Last updated 2025-08-27)*
    - **[API Reference](./guides/infrastructure/cache/api-reference.md)**: Complete API documentation for all cache interfaces and factory methods *(Last updated 2025-08-27)*
    - **[Configuration Guide](./guides/infrastructure/cache/configuration.md)**: Preset system, environment variables, and configuration management *(Last updated 2025-08-27)*
    - **[Testing Guide](./guides/infrastructure/cache/testing.md)**: Testing strategies, fixtures, and performance benchmarks *(Last updated 2025-08-27)*
    - **[Troubleshooting Guide](./guides/infrastructure/cache/troubleshooting.md)**: Performance optimization, debugging workflows, and operational guidance *(Last updated 2025-08-27)*
  - **[Monitoring](./guides/infrastructure/MONITORING.md)**: Comprehensive monitoring and observability capabilities with centralized monitoring, performance analytics, health checks, and metrics collection *(Last updated 2025-07-30)*
  - **[Resilience](./guides/infrastructure/RESILIENCE.md)**: Comprehensive resilience patterns for AI service operations with circuit breakers, retry mechanisms, configuration presets, and performance monitoring *(Last updated 2025-07-30)*
  - **[Security](./guides/infrastructure/SECURITY.md)**: Defense-in-depth security capabilities for AI-powered applications with authentication, authorization, and AI-specific threat protection *(Last updated 2025-07-30)*
- **[Domain Services Guide](./guides/domain-services/README.md)**: Overview and principles for building customizable, infrastructure-powered domain services *(Last updated 2025-08-03)*
  - **[Text Processing](./guides/domain-services/TEXT_PROCESSING.md)**: Comprehensive guide to the educational text processing implementation demonstrating domain service patterns, AI integration, and infrastructure usage *(Last updated 2025-08-03)*
- **[Template Customization Guide](./guides/get-started/TEMPLATE_CUSTOMIZATION.md)**: Guide to understanding the project's architecture for stability and easy customization with clear separation between Infrastructure and Domain logic *(Last updated 2025-07-31)*

### Application Guides

- **[API Documentation](./guides/application/API.md)**: API documentation covering public endpoints, authentication, and internal infrastructure services *(Last updated 2024-07-27)*
- **[FastAPI Backend](./guides/application/BACKEND.md)**: Backend service documentation with API endpoints, setup instructions, and text processing operations *(Last updated 2024-07-27)*
- **[Streamlit Frontend](./guides/application/FRONTEND.md)**: Streamlit frontend documentation covering UI features, API integration, and development setup *(Last updated 2024-07-27)*
- **[Shared Module](./guides/application/SHARED.md)**: Shared module documentation for Pydantic models and sample data used across backend and frontend *(Last updated 2024-07-27)*

### Developer Guides

- **[Authentication & Authorization](./guides/developer/AUTHENTICATION.md)**: Comprehensive authentication and authorization system with multi-key authentication, dual-API architecture protection, and flexible security modes *(Last updated 2025-07-31)*
- **[Code Standards & Examples](./guides/developer/CODE_STANDARDS.md)**: Standardized patterns for code examples, imports, error handling, and architectural guidelines for infrastructure vs domain service separation *(Last updated 2025-07-31)*
- **[Core Module Integration](./guides/developer/CORE_MODULE_INTEGRATION.md)**: Essential guide to the critical integration layer between template infrastructure and custom domain services, covering configuration management, exception handling, and middleware patterns *(Last updated 2025-08-03)*
- **[Deployment](./guides/developer/DEPLOYMENT.md)**: Deployment guide for the dual-API architecture with resilience patterns and infrastructure services across various environments *(Last updated 2025-07-30)*
- **[Docker Setup & Usage](./guides/developer/DOCKER.md)**: Comprehensive Docker setup for development and production environments with backend FastAPI and frontend Streamlit services *(Last updated 2025-07-31)*
- **[Documentation Guidance & Philosophy](./guides/developer/DOCUMENTATION_GUIDANCE.md)**: Documentation philosophy and best practices with hierarchical, purpose-driven approach for contextual and actionable documentation *(Last updated 2025-07-31)*
- **[Exception Handling](./guides/developer/EXCEPTION_HANDLING.md)**: Comprehensive exception handling system with hierarchical error classification, resilience integration, global error handlers, and testing patterns for robust error management *(Last updated 2025-08-05)*
- **[Testing](./guides/testing/TESTING.md)**: Comprehensive testing guide covering unit tests, integration tests, performance tests, and test suite organization for backend and frontend *(Last updated 2025-07-30)*
- **[Virtual Environment Management](./guides/developer/VIRTUAL_ENVIRONMENT_GUIDE.md)**: Enhanced virtual environment management with automatic Python detection and project-level virtual environment creation *(Last updated 2025-07-30)*

### Operations Guides
- **[Backup & Recovery](./guides/operations/BACKUP_RECOVERY.md)**: Comprehensive backup and recovery procedures, disaster recovery workflows, data backup strategies, and configuration preservation for business continuity *(Last updated 2025-08-03)*
- **[Logging Strategy](./guides/operations/LOGGING_STRATEGY.md)**: Structured logging strategies, log analysis procedures, security event logging, and operational log management for effective system observability *(Last updated 2025-08-03)*
- **[Middleware](./guides/operations/MIDDLEWARE.md)**: Comprehensive middleware stack operations guide covering all 9 production-ready middleware components including CORS, security, rate limiting, compression, API versioning, and performance monitoring with configuration management and operational procedures *(Last updated 2025-08-08)*
- **[Monitoring](./guides/operations/MONITORING.md)**: Operational monitoring procedures, health checks, performance monitoring, alert management, and system health verification for production environments *(Last updated 2025-08-03)*
- **[Performance Optimization](./guides/operations/PERFORMANCE_OPTIMIZATION.md)**: Performance optimization procedures, tuning strategies, cache optimization, AI service optimization, and performance testing workflows *(Last updated 2025-08-03)*
- **[Security](./guides/operations/SECURITY.md)**: Comprehensive security guide consolidating authentication, AI-specific security threats, incident response procedures, and production security checklist *(Last updated 2025-08-03)*
- **[Troubleshooting](./guides/operations/TROUBLESHOOTING.md)**: Systematic troubleshooting workflows, diagnostic procedures, and resolution steps for common operational issues with decision trees and escalation procedures *(Last updated 2025-08-03)*

### Miscellaneous

- **[Future Features](./future-features/)**: Roadmaps for planned future features of the template or strategies to extend template for production use.
- **[Additional Documentation Ideas](./DOCS_MORE.md)**: Implementation roadmap for improving template documentation with quick wins, operational guides, and tutorial series *(Last updated 2025-08-02)*
- **[Documentation Index](./DOCS_INDEX.md)**: This file. *(Last updated 2025-08-02)*
  - **[Documentation by Topic](./DOCS_BY_TOPIC.md)**: Browse documentation by topic category, helping you find content related to specific domains. *(Last updated 2025-08-02)*
  - **[Documentation by Audience](./DOCS_BY_AUDIENCE.md)**: Browse documentation by target audience level, helping you find content appropriate for your experience level. *(Last updated 2025-08-02)*

## 📚 Technical Deep Dives

Gemini deep research reports.

- **[FastAPI](./reference/deep-dives/FastAPI.md)**: Comprehensive technical deep-dive into architecture, performance, and application in Large Language Model systems *(Last updated 2025-07-30)*
- **[Streamlit](./reference/deep-dives/Streamlit.md)**: Comprehensive technical analysis of the Python application framework for data and AI applications *(Last updated 2025-07-30)*

## 📦 Code Reference

Automatically generated from Python docstrings and README files within project code.

### [Backend](./code_ref/backend/)

- **[Backend README](./guides/application/BACKEND.md)**: Backend service documentation with API endpoints, setup instructions, and text processing operations *(Last updated 2024-07-27 15:55)*

#### API

- **[API README](./guides/application/API.md)**: API documentation covering public endpoints, authentication, and internal infrastructure services *(Last updated 2024-07-27)*
- **[Resilience API](./code_ref/backend/app/api/internal/resilience/)**: Resilience API documentation with 38 endpoints for configuration management and monitoring *(Last updated 2024-07-27)*

#### Infrastructure

- **[AI](./code_ref/backend/app/infrastructure/ai/)**: AI infrastructure documentation covering input sanitization, prompt building, and security-first design *(Last updated 2024-07-27)*
- **[Cache](./code_ref/backend/app/infrastructure/cache/)**: Cache infrastructure documentation with Redis and memory implementations, performance monitoring *(Last updated 2024-07-27)*
- **[Monitoring](./code_ref/backend/app/infrastructure/monitoring/)**: Comprehensive monitoring and observability infrastructure serving as centralized access point for performance monitoring, health checks, and metrics collection *(Last updated 2025-07-30)*
- **[Resilience](./code_ref/backend/app/infrastructure/resilience/)**: Resilience infrastructure documentation covering circuit breakers, retry mechanisms, and configuration management *(Last updated 2024-07-27)*
- **[Security](./code_ref/backend/app/infrastructure/security/)**: Comprehensive security infrastructure implementing defense-in-depth security practices with configurable authentication, authorization, and input protection *(Last updated 2025-07-30)*

#### Tests & Examples

- **[Backend Testing](./code_ref/backend/tests/)**: Comprehensive test suite documentation with test structure, organization, and testing guidelines *(Last updated 2024-07-27)*
- **[Backend Examples](./code_ref/backend/examples/)**: Infrastructure examples demonstrating advanced usage of resilience and AI components *(Last updated 2024-07-27)*

### [Frontend](./code_ref/frontend/)

- **[Frontend README](./guides/application/FRONTEND.md)**: Streamlit frontend documentation covering UI features, API integration, and development setup *(Last updated 2024-07-27)*

### [Shared Module](./code_ref/shared/)

- **[Shared Module README](./guides/application/SHARED.md)**: Shared module documentation for Pydantic models and sample data used across backend and frontend *(Last updated 2024-07-27)*

### Miscellaneous

- **[Examples Documentation](./code_ref/examples/)**: Comprehensive examples and usage guides demonstrating API integration and HTTP client usage *(Last updated 2024-07-27)*
- **[Scripts Documentation](./code_ref/scripts/)**: Utility scripts for API key generation, health checks, configuration validation, testing, and documentation management *(Last updated 2024-07-27)*
