"""Service-level tests package.

This package contains tests for domain services that work directly with business logic
without HTTP layer interference. Tests at this level can access internal state,
validate service behavior, and test integration with infrastructure services
without the complications of HTTP request/response handling.

Service-level tests are ideal for:
- Testing business logic and domain rules
- Validating integration with infrastructure services
- Accessing internal state and circuit breaker information
- Testing complex workflows and state transitions
- Validating error handling and resilience patterns at service level

Key Testing Areas:
- Text processing operations and business rules
- Circuit breaker state management and transitions
- Resilience pattern behavior and configuration
- Integration with caching and AI infrastructure
- Service-level error handling and fallback mechanisms
"""