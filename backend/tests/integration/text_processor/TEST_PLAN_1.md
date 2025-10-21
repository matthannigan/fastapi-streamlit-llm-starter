# Integration Test Plan for Text Processor Service
## PROMPT 1 - ARCHITECTURAL ANALYSIS

Based on the analysis of `backend/contracts/services/text_processor.pyi` and related infrastructure components, this document identifies critical integration seams that require comprehensive integration testing to ensure the text processing service operates correctly in production environments.

## Summary of 3 Most Important Principles from Integration Testing Documentation

1. **Test Critical Paths, Not Every Path**: Focus integration tests on "critical paths" and high-value user journeys rather than building comprehensive coverage. For text processing, this means testing the complete flow from API request to AI response with all infrastructure components working together.

2. **Trust Contracts, Verify Integrations**: Leverage the existing unit tests that verify individual component contracts, and focus integration tests on verifying that the "seams" or "connections" between components work correctly. The text processor has well-defined contracts with cache, resilience, and AI infrastructure services.

3. **Test from the Outside-In**: Whenever possible, initiate integration tests from the application boundary (HTTP endpoints) and assert on observable outcomes rather than internal implementation details. For text processing, this means testing through the REST API endpoints rather than directly invoking service methods.

## Summary of 3 Most Important Anti-Patterns from Integration Testing Documentation

1. **Testing Internal Implementation Details**: Avoid testing internal method calls, private attributes, or specific algorithms. Focus on observable behavior and outcomes rather than how the text processor internally orchestrates AI calls.

2. **Mocking Internal Collaborators**: Do not mock the text processor's dependencies (cache, resilience, AI services) in integration tests. Use high-fidelity fakes (fakeredis) or real infrastructure to verify actual collaboration patterns.

3. **Brittle Test Setup**: Avoid complex test setups that break when implementation changes. Integration tests should be resilient to refactoring and focus on the external contracts and behavior that matter to users.

## INTEGRATION TEST PLAN (PROMPT 1 - ARCHITECTURAL ANALYSIS)

### 1. SEAM: API → TextProcessorService → Cache → AI Service
   **COMPONENTS**: `/v1/text_processing/process` endpoint, TextProcessorService, AIResponseCache, PydanticAI Agent
   **CRITICAL PATH**: HTTP request → Authentication → Input validation → Cache lookup → AI processing → Response caching → HTTP response
   **TEST SCENARIOS**:
   - Successful text processing with cache miss (full AI processing flow)
   - Successful text processing with cache hit (cache-only flow)
   - Cache failure fallback to direct AI processing
   - AI service failure with graceful degradation and fallback response
   - Cache and AI service both unavailable (full degradation)
   **INFRASTRUCTURE**: fakeredis, test HTTP client, mock AI service (or real test API key)
   **PRIORITY**: HIGH (core user-facing functionality)
   **CONFIDENCE**: HIGH (clear architectural boundary with well-defined contract)

### 2. SEAM: API → TextProcessorService → Resilience Orchestrator → AI Service
   **COMPONENTS**: `/v1/text_processing/process` endpoint, TextProcessorService, AIServiceResilience, CircuitBreaker, Retry mechanisms
   **CRITICAL PATH**: HTTP request → Resilience pattern application → AI service call with retry/circuit breaker → Response handling
   **TEST SCENARIOS**:
   - AI service transient failure with successful retry
   - AI service persistent failure triggering circuit breaker
   - Circuit breaker open state with fast failure
   - Circuit breaker half-open state with recovery testing
   - Different resilience strategies per operation (aggressive for sentiment, conservative for Q&A)
   **INFRASTRUCTURE**: Configurable failure simulation, resilience monitoring endpoints
   **PRIORITY**: HIGH (service reliability and user experience)
   **CONFIDENCE**: HIGH (resilience patterns are critical infrastructure)

### 3. SEAM: API → TextProcessorService → Input Sanitizer → Response Validator
   **COMPONENTS**: `/v1/text_processing/process` endpoint, TextProcessorService, PromptSanitizer, ResponseValidator
   **CRITICAL PATH**: HTTP request → Input sanitization → AI processing → Response validation → HTTP response
   **TEST SCENARIOS**:
   - Input sanitization blocks prompt injection attempts
   - Input sanitization preserves valid text content
   - Response validator blocks harmful AI responses
   - Response validator passes safe AI responses
   - Both security layers working together prevent threats
   **INFRASTRUCTURE**: Malicious input samples, harmful response simulation
   **PRIORITY**: HIGH (security-critical integration)
   **CONFIDENCE**: HIGH (security is non-negotiable requirement)

### 4. SEAM: API → TextProcessorService → Batch Processing Concurrency
   **COMPONENTS**: `/v1/text_processing/batch_process` endpoint, TextProcessorService, asyncio.Semaphore, individual request processing
   **CRITICAL PATH**: HTTP batch request → Concurrency limiting → Parallel processing → Aggregate response → HTTP response
   **TEST SCENARIOS**:
   - Successful batch processing with all requests succeeding
   - Batch processing with mixed success/failure results
   - Concurrency limit enforcement under high load
   - Individual request isolation (one failure doesn't affect others)
   - Batch performance metrics and timing accuracy
   **INFRASTRUCTURE**: Test data generation, performance monitoring, concurrency validation
   **PRIORITY**: MEDIUM (important for efficiency but less critical than single requests)
   **CONFIDENCE**: HIGH (well-defined batch processing contract)

### 5. SEAM: TextProcessorService → Cache → Resilience Orchestrator (Cache Operations)
   **COMPONENTS**: TextProcessorService, AIResponseCache, Resilience patterns for cache operations
   **CRITICAL PATH**: Service request → Cache operation → Resilience application → Cache response
   **TEST SCENARIOS**:
   - Cache operations protected by circuit breaker
   - Cache retry patterns on temporary failures
   - Cache performance monitoring integration
   - Cache degradation handling (Redis unavailable → memory fallback)
   **INFRASTRUCTURE**: Cache failure simulation, resilience monitoring
   **PRIORITY**: MEDIUM (cache reliability affects performance but not core functionality)
   **CONFIDENCE**: MEDIUM (may be internal implementation detail - verify with unit test analysis)

### 6. SEAM: API → Authentication → TextProcessorService (Authorization Flow)
   **COMPONENTS**: `/v1/text_processing/*` endpoints, APIKeyAuth, TextProcessorService
   **CRITICAL PATH**: HTTP request → API key validation → Service invocation → Response
   **TEST SCENARIOS**:
   - Valid API key enables access to all text processing operations
   - Invalid API key properly rejects requests
   - Missing API key properly rejects requests
   - Authentication works across all text processing endpoints
   - Optional authentication works for discovery endpoints
   **INFRASTRUCTURE**: Test API keys, authentication middleware
   **PRIORITY**: HIGH (security-critical for protected operations)
   **CONFIDENCE**: HIGH (security boundary is well-defined)

### 7. SEAM: TextProcessorService → AI Agent → Model Configuration
   **COMPONENTS**: TextProcessorService, PydanticAI Agent, model settings, prompt templates
   **CRITICAL PATH**: Service request → AI agent invocation → Model configuration → Prompt construction → AI response
   **TEST SCENARIOS**:
   - Different AI operations use appropriate model settings
   - Prompt templates are correctly parameterized with user input
   - Model configuration changes affect AI responses appropriately
   - AI agent error handling and response parsing
   **INFRASTRUCTURE**: Model configuration overrides, prompt template validation
   **PRIORITY**: MEDIUM (AI integration is core but model-specific)
   **CONFIDENCE**: MEDIUM (may be internal implementation - depends on abstractions)

### 8. SEAM: Internal API → TextProcessorService Health Monitoring
   **COMPONENTS**: `/v1/text_processing/health` endpoint, TextProcessorService, resilience health monitoring
   **CRITICAL PATH**: Health check request → Service health assessment → Infrastructure health check → Aggregate health response
   **TEST SCENARIOS**:
   - Health endpoint reflects actual service health status
   - Health endpoint integrates resilience orchestrator health data
   - Health endpoint handles service degradation gracefully
   - Health monitoring provides actionable operational data
   **INFRASTRUCTURE**: Health check validation, operational monitoring
   **PRIORITY**: LOW (operational monitoring, not user-facing)
   **CONFIDENCE**: MEDIUM (health check patterns are fairly standard)

### 9. SEAM: TextProcessorService → Operation Registry → Configuration Management
   **COMPONENTS**: TextProcessorService, operation configuration registry, resilience strategy mapping
   **CRITICAL PATH**: Service initialization → Operation registry loading → Strategy assignment → Runtime operation dispatch
   **TEST SCENARIOS**:
   - Operation registry correctly maps operations to handlers
   - Resilience strategies are correctly applied per operation type
   - Configuration changes are properly applied at runtime
   - Invalid operation configurations are handled gracefully
   **INFRASTRUCTURE**: Configuration validation, operation registry testing
   **PRIORITY**: LOW (configuration management, typically stable)
   **CONFIDENCE**: LOW (likely internal implementation detail - confirm with unit tests)

### 10. SEAM: TextProcessorService → Monitoring/Logging Infrastructure
   **COMPONENTS**: TextProcessorService, logging infrastructure, request tracing, performance monitoring
   **CRITICAL PATH**: Service request → Request ID generation → Processing logging → Performance metrics → Response logging
   **TEST SCENARIOS**:
   - Request IDs are properly generated and propagated
   - Processing events are logged with appropriate detail
   - Performance metrics are collected and accurate
   - Error conditions are properly logged for debugging
   - Log structure supports operational monitoring
   **INFRASTRUCTURE**: Log capture validation, metrics verification
   **PRIORITY**: LOW (monitoring infrastructure, not core functionality)
   **CONFIDENCE**: MEDIUM (logging patterns are important but fairly standard)

## PRIORITIZATION SUMMARY

### HIGH PRIORITY (P0) - Critical User Journeys
1. **API → TextProcessorService → Cache → AI Service** (Core text processing flow)
2. **API → TextProcessorService → Resilience Orchestrator → AI Service** (Service reliability)
3. **API → TextProcessorService → Input Sanitizer → Response Validator** (Security)
4. **API → Authentication → TextProcessorService** (Authorization)

### MEDIUM PRIORITY (P1) - Important Features
5. **API → TextProcessorService → Batch Processing Concurrency** (Batch efficiency)
6. **TextProcessorService → Cache → Resilience Orchestrator** (Cache reliability)
7. **TextProcessorService → AI Agent → Model Configuration** (AI integration)

### LOW PRIORITY (P2) - Operational Concerns
8. **Internal API → TextProcessorService Health Monitoring** (Health checks)
9. **TextProcessorService → Operation Registry → Configuration** (Configuration management)
10. **TextProcessorService → Monitoring/Logging Infrastructure** (Logging/metrics)

## IMPLEMENTATION NOTES

### Critical Success Factors
- **Use HTTP Client for Outside-In Testing**: Test through FastAPI TestClient to verify complete request/response cycles
- **High-Fidelity Infrastructure**: Use fakeredis for cache testing, real resilience orchestrator for reliability testing
- **Environment Variable Testing**: Use monkeypatch for environment configuration testing per project standards
- **Behavior-Focused Assertions**: Verify response structures, status codes, and timing rather than internal state

### Infrastructure Requirements
- **fakeredis**: For Redis cache simulation with high fidelity
- **Test HTTP Client**: FastAPI TestClient for API-level testing
- **Resilience Monitoring**: Access to resilience orchestrator health endpoints
- **Configuration Flexibility**: Ability to override AI model settings, cache settings, and resilience parameters

### Test Data Requirements
- **Valid Text Samples**: Various lengths and content types for testing
- **Malicious Inputs**: Prompt injection attempts for security testing
- **AI Failure Scenarios**: Configurable AI service failure simulation
- **Batch Data**: Mixed operation types for batch processing tests

## NEXT STEPS

This integration test plan should be validated against existing unit tests to:
1. Confirm which seams are actually used in practice
2. Identify any missing integration opportunities
3. Refine confidence levels based on actual implementation patterns
4. Prioritize implementation based on business value and technical risk

The plan provides a comprehensive foundation for implementing robust integration tests that verify the text processing service works correctly with all its infrastructure dependencies while maintaining focus on user-visible behavior and system reliability.