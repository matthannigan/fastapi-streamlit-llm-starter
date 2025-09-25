# Documentation by Topic

This view organizes all documentation by topic category, providing an alternative navigation structure to help you find content related to specific domains.

*Last updated on 2025-09-25*

## Application

- **[API Documentation](guides/application/API.md)**: API documentation covering public endpoints, authentication, and internal infrastructure services

- **[FastAPI Backend - Production-Ready AI Text Processing API](guides/application/BACKEND.md)**: Backend service documentation with API endpoints, setup instructions, and text processing operations

- **[Shared Module](guides/application/SHARED.md)**: Shared module documentation for Pydantic models and sample data used across backend and frontend

- **[Streamlit Frontend - AI Text Processing Interface](guides/application/FRONTEND.md)**: Streamlit frontend documentation covering UI features, API integration, and development setup


## Architecture

- **[Dual API Architecture](reference/key-concepts/DUAL_API_ARCHITECTURE.md)**: Sophisticated dual-API architecture that separates external business operations from internal infrastructure management with clear boundaries

- **[Infrastructure vs Domain Services](reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)**: Architectural distinction between reusable template components and application-specific business logic for maintaining template reusability


## Customization

- **[Template Customization](/guides/get-started/TEMPLATE_CUSTOMIZATION.md)**: Guide to understanding the project's architecture for stability and easy customization with clear separation between Infrastructure and Domain logic


## Deployment

- **[Deployment Guide](guides/developer/DEPLOYMENT.md)**: Deployment guide for the dual-API architecture with resilience patterns and infrastructure services across various environments


## Developer

- **[API Authentication & Authorization](guides/developer/AUTHENTICATION.md)**: Comprehensive authentication and authorization system with multi-key authentication, dual-API architecture protection, and flexible security modes

- **[Code Standards & Examples](guides/developer/CODE_STANDARDS.md)**: Standardized patterns for code examples, imports, error handling, and architectural guidelines for infrastructure vs domain service separation

- **[Core Module Integration Guide](guides/developer/CORE_MODULE_INTEGRATION.md)**: Essential guide to the critical integration layer between template infrastructure and custom domain services, covering configuration management, exception handling, and enhanced middleware patterns

- **[Docker Setup & Usage](guides/developer/DOCKER.md)**: Comprehensive Docker setup for development and production environments with backend FastAPI and frontend Streamlit services

- **[Documentation Guidance & Philosophy](guides/developer/DOCUMENTATION_GUIDANCE.md)**: Documentation philosophy and best practices with hierarchical, purpose-driven approach for contextual and actionable documentation

- **[Exception Handling Guide](guides/developer/EXCEPTION_HANDLING.md)**: Comprehensive exception handling system with hierarchical error classification, resilience integration, global error handlers, and testing patterns for robust error management

- **[Virtual Environment Management](guides/developer/VIRTUAL_ENVIRONMENT_GUIDE.md)**: Enhanced virtual environment management with automatic Python detection and project-level virtual environment creation


## Domain Services

- **[Domain Services Guide](guides/domain-services/README.md)**: Overview and principles for building customizable, infrastructure-powered domain services

- **[Text Processing Domain Service](guides/domain-services/TEXT_PROCESSING.md)**: Comprehensive guide to the educational text processing implementation demonstrating domain service patterns, AI integration, and infrastructure usage


## Infrastructure

- **[AI Infrastructure Service](guides/infrastructure/AI.md)**: Production-ready, security-first AI infrastructure service with comprehensive protection against prompt injection attacks and flexible templating

- **[Cache Infrastructure API Reference](guides/infrastructure/cache/api-reference.md)**: Comprehensive API reference documentation for all public APIs and interfaces in the cache infrastructure including CacheFactory, configuration APIs, and dependency injection functions

- **[Cache Infrastructure Comprehensive Usage Guide](guides/infrastructure/cache/usage-guide.md)**: Complete practical usage guide for the cache infrastructure - from 5-minute quickstart to advanced optimization patterns with preset-based configuration

- **[Cache Infrastructure Configuration Guide](guides/infrastructure/cache/configuration.md)**: Flexible, production-ready configuration through modern preset-based system that simplifies setup from 28+ environment variables to 1-4 essential settings

- **[Cache Infrastructure Performance & Troubleshooting Guide](guides/infrastructure/cache/troubleshooting.md)**: Systematic troubleshooting workflows, performance optimization strategies, and emergency procedures for cache infrastructure with debugging workflows and resolution procedures

- **[Cache Infrastructure Service](guides/infrastructure/cache/CACHE.md)**: Multi-tiered caching capabilities optimized for AI response caching with intelligent strategies, monitoring, and graceful degradation - primary entry point for cache documentation

- **[Cache Infrastructure Testing Guide](guides/infrastructure/cache/testing.md)**: Comprehensive testing strategies, patterns, and best practices including unit tests, integration tests, and CI/CD configuration

- **[Environment Detection Service](guides/developer/ENVIRONMENT_DETECTION.md)**: Unified environment detection service providing centralized environment classification across all backend infrastructure services with confidence scoring and feature-aware detection

- **[Monitoring Infrastructure Service](guides/infrastructure/MONITORING.md)**: Comprehensive monitoring and observability capabilities with centralized monitoring, performance analytics, health checks, and metrics collection

- **[Resilience Infrastructure Service](guides/infrastructure/RESILIENCE.md)**: Comprehensive resilience patterns for AI service operations with circuit breakers, retry mechanisms, configuration presets, and performance monitoring

- **[Security Infrastructure Service](guides/infrastructure/SECURITY.md)**: Defense-in-depth security capabilities for AI-powered applications with authentication, authorization, and AI-specific threat protection


## Operations

- **[Backup & Recovery Guide](guides/operations/BACKUP_RECOVERY.md)**: Comprehensive backup and recovery procedures, disaster recovery workflows, data backup strategies, and configuration preservation for business continuity

- **[Logging Strategy Guide](guides/operations/LOGGING_STRATEGY.md)**: Structured logging strategies, log analysis procedures, security event logging, and operational log management for effective system observability

- **[Middleware Operations Guide](guides/operations/MIDDLEWARE.md)**: Comprehensive middleware stack operations guide covering all 9 production-ready middleware components including CORS, security, rate limiting, compression, API versioning, and performance monitoring with configuration management and operational procedures

- **[Operational Monitoring Guide](guides/operations/MONITORING.md)**: Operational monitoring procedures, health checks, performance monitoring, middleware monitoring, alert management, and system health verification for production environments

- **[Performance Optimization Guide](guides/operations/PERFORMANCE_OPTIMIZATION.md)**: Performance optimization procedures, tuning strategies, cache optimization, middleware performance optimization, AI service optimization, and performance testing workflows

- **[Troubleshooting Guide](guides/operations/TROUBLESHOOTING.md)**: Systematic troubleshooting workflows, diagnostic procedures, and resolution steps for common operational issues with decision trees and escalation procedures


## Security

- **[Security Guide](guides/operations/SECURITY.md)**: Comprehensive security guide consolidating authentication, middleware security integration, AI-specific security threats, incident response procedures, and production security checklist


## Setup

- **[Get Started Checklist](get-started/CHECKLIST.md)**: Complete installation and setup checklist covering initial setup, API keys, Docker configuration, and development workflows

- **[Setup & Complete Systems Integration Guide](get-started/SETUP_INTEGRATION.md)**: Comprehensive setup and system integration guide with complete usage examples to get up and running quickly


## Testing

- **[Contributing Tests Guide](guides/testing/CONTRIBUTING_TESTS.md)**: Guidelines and standards for adding new tests to the project, ensuring consistency with testing philosophy and maintaining test quality

- **[Coverage Strategy Guide](guides/testing/COVERAGE_STRATEGY.md)**: Tiered coverage approach emphasizing meaningful metrics over raw percentages, focusing on critical path coverage and quality indicators

- **[Integration Tests Comprehensive Guide](guides/testing/INTEGRATION_TESTS.md)**: Complete guide to component collaboration and seam testing strategies with high-fidelity environment testing, boundary verification, and collaborative behavior validation

- **[Mocking Strategy Guide](guides/testing/MOCKING_GUIDE.md)**: Strategic approach to mocking emphasizing fakes over mocks, boundary mocking patterns, and maintaining test integrity through minimal mock usage

- **[Test Execution Guide](guides/testing/TEST_EXECUTION_GUIDE.md)**: Practical guide to running tests, debugging failures, troubleshooting common issues, and maintaining test execution environments

- **[Test Structure Guide](guides/testing/TEST_STRUCTURE.md)**: Test organization patterns, fixture strategies, test categorization, and structural approaches for maintainable test suites

- **[Testing Overview](guides/testing/TESTING.md)**: High-level testing philosophy overview with navigation to comprehensive testing guides for unit tests, integration tests, and testing workflows

- **[Unit Tests Comprehensive Guide](guides/testing/UNIT_TESTS.md)**: Complete guide to behavior-driven unit testing with 3-pillar framework, 5-step AI workflow process, testing patterns, and quality framework for isolated component verification

- **[Writing Tests Guide](guides/testing/WRITING_TESTS.md)**: Docstring-driven test development principles focusing on contract-based testing, behavior verification, and maintainable test design patterns

