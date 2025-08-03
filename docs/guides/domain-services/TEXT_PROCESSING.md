# Text Processing Domain Service

## Overview

The Text Processing Domain Service is an **educational example** designed to demonstrate how to build a robust, production-ready AI text processing service using the FastAPI + Streamlit LLM Starter Template. This service showcases comprehensive patterns for AI-powered text processing, highlighting the integration of infrastructure services with domain-specific logic.

### Purpose and Learning Objectives

This domain service provides a complete, production-ready implementation of AI text processing operations that serves as both a functional component and a learning resource. By studying this implementation, developers will learn:

- How to design scalable, resilient text processing services
- Integration patterns for AI infrastructure services
- Comprehensive error handling and validation strategies
- Batch processing implementation
- Resilience and fallback mechanisms
- Security best practices for AI-powered services

## Architectural Overview

### Design Philosophy

The Text Processing Domain Service embodies the project's core architectural principles:

1. **Infrastructure vs Domain Separation**: 
   - Domain Service (`app/services/text_processor.py`): Business logic and AI processing
   - Infrastructure Services: Provide caching, resilience, security, and AI integration

2. **Resilience-First Design**:
   - Multiple layers of error handling
   - Configurable circuit breakers and retry mechanisms
   - Graceful degradation strategies
   - Comprehensive fallback responses

3. **Security-Driven Implementation**:
   - Input sanitization
   - Response validation
   - Secure prompt construction
   - Comprehensive logging and tracing

### Service Architecture Layers

```
┌─────────────────────────────────────────┐
│ Text Processing Domain Service          │
│                                         │
│ 1. Input Layer: Sanitization           │
│ 2. Caching Layer: Response Lookup      │
│ 3. AI Processing Layer: Model Calls    │
│ 4. Resilience Layer: Error Handling    │
│ 5. Validation Layer: Safety Checks     │
│ 6. Fallback Layer: Degraded Responses  │
└─────────────────────────────────────────┘
```

## Core Components

### Supported Operations

The Text Processing Domain Service supports five primary AI-powered operations:

1. **Summarization**
   - Generate concise summaries of input text
   - Configurable summary length
   - Intelligent text condensation

2. **Sentiment Analysis**
   - Analyze emotional tone of text
   - Provide confidence scores
   - Detect nuanced sentiment

3. **Key Points Extraction**
   - Identify most important points
   - Configurable number of points
   - Retain essential information

4. **Question Generation**
   - Create thoughtful questions from text
   - Configurable number of questions
   - Encourage deeper text understanding

5. **Question Answering**
   - Answer specific questions about text
   - Context-aware responses
   - Requires explicit question parameter

## Infrastructure Integration

### Resilience Patterns

The service implements three primary resilience strategies:

1. **Aggressive Strategy**
   - Fastest failure detection
   - Immediate fallback
   - Ideal for time-sensitive operations like sentiment analysis
   - Minimal retry attempts

2. **Balanced Strategy**
   - Moderate retry attempts
   - Reasonable timeouts
   - Default for most operations
   - Provides good performance and reliability

3. **Conservative Strategy**
   - Extended retry attempts
   - Longer timeout windows
   - Used for critical operations like question answering
   - Prioritizes completeness over speed

### Caching Mechanism

The service leverages a sophisticated caching system with the following features:

- **Intelligent Caching**: Reduces redundant AI calls
- **Multi-layered Storage**:
  - Redis-backed primary cache
  - Fallback in-memory cache
- **Configurable TTL (Time-To-Live)**
- **Operation-Specific Caching**
- **Comprehensive Cache Metrics**

### Security Implementation

Security is implemented through multiple layers:

1. **Input Sanitization**
   - Prevent prompt injection
   - Remove potentially malicious content
   - Normalize input text

2. **Prompt Construction**
   - Use secure, parameterized prompt templates
   - Prevent direct text interpolation
   - Add additional safety instructions

3. **Response Validation**
   - Validate AI model outputs
   - Ensure response structure and content safety
   - Reject potentially harmful responses

4. **Comprehensive Logging**
   - Capture all processing events
   - Mask sensitive information
   - Provide audit trail for security analysis

## Batch Processing

### Concurrent Processing Architecture

```
┌─────────────────────────────────┐
│ Batch Processing Workflow       │
│                                 │
│ 1. Request Validation           │
│ 2. Concurrent Task Execution    │
│ 3. Semaphore-Based Concurrency  │
│ 4. Comprehensive Error Handling │
│ 5. Aggregated Result Generation │
└─────────────────────────────────┘
```

Key Batch Processing Features:
- Configurable concurrency limits
- Asynchronous processing
- Individual request tracking
- Comprehensive error management
- Batch-level status reporting

## Performance Considerations

### Performance Optimization Strategies

1. **Concurrent Processing**
   - Async/await design
   - Semaphore-controlled concurrency
   - Minimize blocking operations

2. **Intelligent Caching**
   - Reduce redundant AI model calls
   - Cache operation-specific results
   - Configurable cache expiration

3. **Efficient Resource Management**
   - Configurable batch size limits
   - Circuit breaker integration
   - Graceful degradation mechanisms

### Performance Metrics

The service tracks comprehensive performance metrics:
- Processing times per operation
- Cache hit/miss ratios
- Resilience pattern statistics
- Error rates and fallback usage

## Customization Guide

### Replacing the Domain Service

When using this template for your project:

1. **Keep Infrastructure Services**
   - Preserve caching mechanisms
   - Maintain resilience patterns
   - Retain security implementations

2. **Modify Domain Logic**
   - Replace text processing operations
   - Customize AI model integration
   - Adapt to your specific use cases

3. **Maintain Architectural Patterns**
   - Follow existing error handling
   - Preserve dependency injection
   - Maintain input/output schemas

### Configuration Options

```python
# Configurable via settings
settings.BATCH_AI_CONCURRENCY_LIMIT = 10
settings.MAX_BATCH_REQUESTS_PER_CALL = 50
settings.DEFAULT_RESILIENCE_STRATEGY = 'balanced'
```

## Best Practices

1. **Always validate and sanitize inputs**
2. **Implement comprehensive error handling**
3. **Use resilience decorators**
4. **Leverage caching intelligently**
5. **Monitor and log comprehensively**

## Related Documentation

- [Infrastructure vs Domain Services](/docs/reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)
- [Dual API Architecture](/docs/reference/key-concepts/DUAL_API_ARCHITECTURE.md)
- [Resilience Patterns](/docs/guides/infrastructure/RESILIENCE.md)
- [Security Implementations](/docs/guides/infrastructure/SECURITY.md)

## Conclusion

The Text Processing Domain Service serves as both a functional component and an educational resource, demonstrating how to build robust, secure, and performant AI-powered services using modern software engineering practices.

**Remember**: This is an *example implementation*. Study the patterns, understand the architectural principles, and customize for your specific requirements.