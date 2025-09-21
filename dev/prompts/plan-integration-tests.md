First, thoroughly review @INTEGRATION_TESTS.md and @WRITING_TESTS.md.

Now, analyze `backend/contracts` to identify integration test opportunities for the component defined by `backend/contracts/services/text_processor.pyi`. Create a comprehensive test plan following our integration testing philosophy and save it to `backend/tests/integration/text_processor/test_plan.md`.

**ANALYSIS OBJECTIVES:**
1. Identify critical seams between components that require integration testing
2. Map data flows that cross component boundaries
3. Find API endpoints that orchestrate multiple services
4. Locate infrastructure abstractions that need contract verification
5. Identify resilience patterns that require integration validation

**SEAM IDENTIFICATION METHODS:**
- Start at Application Boundaries: Find all API endpoints, message queue consumers, scheduled jobs
- Infrastructure Abstractions: Identify interfaces for cache, database, external services
- Data Flow Tracking: Follow critical domain objects through the system
- Import Analysis: Map dependencies between major components

**TEST PLAN OUTPUT FORMAT:**
For each identified integration point, provide:
1. SEAM NAME: Clear description of the integration boundary
2. COMPONENTS: List of components involved in the integration
3. CRITICAL PATH: The data/control flow being tested
4. TEST SCENARIOS: Specific scenarios to validate
5. INFRASTRUCTURE NEEDS: Required test fixtures (fakeredis, test DB, etc.)
6. PRIORITY: High/Medium/Low based on business criticality

**PRIORITIZATION CRITERIA:**
- HIGH: User-facing features, payment flows, authentication, data persistence
- MEDIUM: Caching layers, monitoring, non-critical workflows
- LOW: Admin features, reporting, nice-to-have optimizations

**EXAMPLE OUTPUT:**
```
INTEGRATION TEST PLAN

1. SEAM: API → TextProcessingService → Cache → Database
   COMPONENTS: /v1/process endpoint, TextProcessingService, RedisCache, JobRepository
   CRITICAL PATH: User request → Processing → Caching → Persistence
   TEST SCENARIOS:
   - Successful processing with cache hit
   - Successful processing with cache miss
   - Cache failure fallback to direct processing
   - Database persistence after processing
   INFRASTRUCTURE: fakeredis, test database
   PRIORITY: HIGH (core user feature)

2. SEAM: AuthMiddleware → SecurityService → EnvironmentDetector
   COMPONENTS: verify_api_key_http, APIKeyAuth, get_environment_info
   CRITICAL PATH: Request → Authentication → Environment-based rules
   TEST SCENARIOS:
   - Valid API key in production environment
   - Missing API key in production (should fail)
   - Development environment bypass
   INFRASTRUCTURE: None (in-memory)
   PRIORITY: HIGH (security critical)
```

**FOCUS ON:**
- Multi-component workflows that users depend on
- Infrastructure integration points
- Error handling and resilience patterns
- Security and authentication flows
- Performance-critical paths with caching/optimization

Generate a prioritized test plan that covers the most critical integration points first.