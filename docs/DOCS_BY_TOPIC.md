# Documentation by Topic

This view organizes all documentation by topic category, providing an alternative navigation structure to help you find content related to specific domains.

*Last updated on 2025-08-03*

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

- **[Core Module Integration Guide](guides/developer/CORE_MODULE_INTEGRATION.md)**: Essential guide to the critical integration layer between template infrastructure and custom domain services, covering configuration management, exception handling, and middleware patterns

- **[Docker Setup & Usage](guides/developer/DOCKER.md)**: Comprehensive Docker setup for development and production environments with backend FastAPI and frontend Streamlit services

- **[Documentation Guidance & Philosophy](guides/developer/DOCUMENTATION_GUIDANCE.md)**: Documentation philosophy and best practices with hierarchical, purpose-driven approach for contextual and actionable documentation

- **[Testing Guide](guides/developer/TESTING.md)**: Comprehensive testing guide covering unit tests, integration tests, performance tests, and test suite organization for backend and frontend

- **[Virtual Environment Management](guides/developer/VIRTUAL_ENVIRONMENT_GUIDE.md)**: Enhanced virtual environment management with automatic Python detection and project-level virtual environment creation


## Infrastructure

- **[AI Infrastructure Service](guides/infrastructure/AI.md)**: Production-ready, security-first AI infrastructure service with comprehensive protection against prompt injection attacks and flexible templating

- **[Cache Infrastructure Service](guides/infrastructure/CACHE.md)**: Multi-tiered caching capabilities optimized for AI response caching with intelligent strategies, monitoring, and graceful degradation

- **[Monitoring Infrastructure Service](guides/infrastructure/MONITORING.md)**: Comprehensive monitoring and observability capabilities with centralized monitoring, performance analytics, health checks, and metrics collection

- **[Resilience Infrastructure Service](guides/infrastructure/RESILIENCE.md)**: Comprehensive resilience patterns for AI service operations with circuit breakers, retry mechanisms, configuration presets, and performance monitoring

- **[Security Infrastructure Service](guides/infrastructure/SECURITY.md)**: Defense-in-depth security capabilities for AI-powered applications with authentication, authorization, and AI-specific threat protection


## Operations

- **[Backup & Recovery Guide](guides/operations/BACKUP_RECOVERY.md)**: Comprehensive backup and recovery procedures, disaster recovery workflows, data backup strategies, and configuration preservation for business continuity

- **[Logging Strategy Guide](guides/operations/LOGGING_STRATEGY.md)**: Structured logging strategies, log analysis procedures, security event logging, and operational log management for effective system observability

- **[Operational Monitoring Guide](guides/operations/MONITORING.md)**: Operational monitoring procedures, health checks, performance monitoring, alert management, and system health verification for production environments

- **[Performance Optimization Guide](guides/operations/PERFORMANCE_OPTIMIZATION.md)**: Performance optimization procedures, tuning strategies, cache optimization, AI service optimization, and performance testing workflows

- **[Troubleshooting Guide](guides/operations/TROUBLESHOOTING.md)**: Systematic troubleshooting workflows, diagnostic procedures, and resolution steps for common operational issues with decision trees and escalation procedures


## Security

- **[Security Guide](guides/operations/SECURITY.md)**: Comprehensive security guide consolidating authentication, AI-specific security threats, incident response procedures, and production security checklist


## Setup

- **[Get Started Checklist](get-started/CHECKLIST.md)**: Complete installation and setup checklist covering initial setup, API keys, Docker configuration, and development workflows

- **[Setup & Complete Systems Integration Guide](get-started/SETUP_INTEGRATION.md)**: Comprehensive setup and system integration guide with complete usage examples to get up and running quickly

