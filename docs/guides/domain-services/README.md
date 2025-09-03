# Domain Services Guide

## Overview

Domain Services in this template represent the business-specific logic and processing capabilities that are built on top of the production-ready infrastructure services. Unlike the stable, reusable infrastructure components, domain services are designed to be:

- **Customizable**: Easily replaceable with your specific business logic
- **Educational**: Demonstrate best practices for integrating infrastructure services
- **Flexible**: Serve as complete examples of how to build complex, AI-powered services

## Key Principles

### Infrastructure vs Domain Services

- **Infrastructure Services** (keep and extend): 
  - Business-agnostic, reusable technical capabilities
  - >90% test coverage
  - Stable APIs with minimal breaking changes
  - Location: `app/infrastructure/`

- **Domain Services** (replace with your logic):
  - Business-specific implementations
  - >70% test coverage
  - Designed to be customized per project
  - Location: `app/services/`

### Current Domain Service Examples

#### Text Processing Service

The Text Processing Service serves as a comprehensive example of a domain service that leverages multiple infrastructure services:

- **AI Integration**: Demonstrates secure AI model interactions
- **Resilience Patterns**: Shows circuit breaker and retry mechanism usage
- **Error Handling**: Provides structured error management
- **Validation**: Implements input sanitization and business rule enforcement

📖 **Detailed Reference**: [Text Processing API Documentation](guides/application/API#text-processing-operations)

## Customization Guidelines

When replacing domain services:

1. **Study the Patterns**
   - Understand how infrastructure services are integrated
   - Maintain error handling and validation approaches
   - Keep the resilience and monitoring integrations

2. **Replace Business Logic**
   - Modify `TextProcessorService` in `app/services/text_processor.py`
   - Add your specific processing operations
   - Maintain the existing service interface

3. **Update Schemas**
   - Modify `app/schemas/text_processing.py`
   - Define your specific request and response models
   - Ensure compatibility with infrastructure services

4. **Extend Test Coverage**
   - Maintain >70% test coverage
   - Add tests for your specific business logic
   - Validate integration with infrastructure services

## Related Documentation

- [Infrastructure vs Domain Services](/docs/reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)
- [Core Module Integration](/docs/guides/developer/CORE_MODULE_INTEGRATION.md)
- [Testing Guide](/docs/guides/testing/TESTING.md)

## Future Extensibility

Future versions of the template may include:
- More domain service examples
- Generalized templates for different AI processing tasks
- Enhanced infrastructure integration patterns

**Remember**: Domain services are your opportunity to implement unique business logic while leveraging the template's robust infrastructure.