# Middleware Integration Testing

## Prompt 1: Identify Integration Test Opportunities and Create Test Plans

Leverage prior work from `backend/tests/integration/middleware/TEST_RECS.md` and analyze `middleware` implementation, including `backend/contracts/core/middleware/*.pyi` and `backend/app/main.py` to identify integration test opportunities and create a comprehensive test plan following our integration testing philosophy.

Unlike most integration tests, we will be building our middleware integration testing suite PRIOR to unit testing.

Save the output to `backend/tests/integration/middleware/TEST_PLAN_DRAFT.md`

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
7. CONFIDENCE: High/Medium/Low based on architectural clarity
   - HIGH: Clear architectural boundary with known integration risks
   - MEDIUM: Potential integration point, verify with unit test analysis (Prompt 3)
   - LOW: May be internal implementation detail, confirm before testing

**PRIORITIZATION CRITERIA:**
- HIGH: User-facing features, payment flows, authentication, data persistence
- MEDIUM: Caching layers, monitoring, non-critical workflows
- LOW: Admin features, reporting, nice-to-have optimizations

**EXAMPLE OUTPUT:**
```markdown
INTEGRATION TEST PLAN (PROMPT 1 - ARCHITECTURAL ANALYSIS)

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
   CONFIDENCE: HIGH (clear architectural boundary)

2. SEAM: AuthMiddleware → SecurityService → EnvironmentDetector
   COMPONENTS: verify_api_key_http, APIKeyAuth, get_environment_info
   CRITICAL PATH: Request → Authentication → Environment-based rules
   TEST SCENARIOS:
   - Valid API key in production environment
   - Missing API key in production (should fail)
   - Development environment bypass
   INFRASTRUCTURE: None (in-memory)
   PRIORITY: HIGH (security critical)
   CONFIDENCE: HIGH (security-critical integration)

3. SEAM: TextProcessingService → PromptBuilder
   COMPONENTS: TextProcessingService, PromptBuilder
   CRITICAL PATH: Service → Prompt construction → AI call
   TEST SCENARIOS:
   - Verify prompt includes user text and operation
   INFRASTRUCTURE: None
   PRIORITY: MEDIUM
   CONFIDENCE: MEDIUM (may be internal detail, check unit tests in Prompt 3)
```

**FOCUS ON:**
- Multi-component workflows that users depend on
- Infrastructure integration points
- Error handling and resilience patterns
- Security and authentication flows
- Performance-critical paths with caching/optimization

Generate a prioritized test plan that covers the most critical integration points first.
