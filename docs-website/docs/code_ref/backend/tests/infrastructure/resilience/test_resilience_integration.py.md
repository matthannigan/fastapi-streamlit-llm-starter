# Comprehensive tests for the resilience service integration.

  file_path: `backend/tests/infrastructure/resilience/test_resilience_integration.py`

Note: Some tests in this file assume domain-specific operations (summarize, sentiment, etc.)
are registered. In practice, these operations would be registered by domain services
like TextProcessorService during initialization.
