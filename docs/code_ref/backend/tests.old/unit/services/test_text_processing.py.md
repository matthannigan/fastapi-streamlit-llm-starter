---
sidebar_label: test_text_processing
---

## TestTextProcessorService

Test the TextProcessorService class.

### service()

```python
def service(self, mock_ai_agent, mock_cache_service, mock_settings, monkeypatch):
```

Create a TextProcessorService instance.

### test_summarize_text()

```python
async def test_summarize_text(self, service, sample_text):
```

Test text summarization.

### test_sentiment_analysis()

```python
async def test_sentiment_analysis(self, service, sample_text):
```

Test sentiment analysis.

### test_sentiment_analysis_invalid_json()

```python
async def test_sentiment_analysis_invalid_json(self, service, sample_text):
```

Test sentiment analysis with invalid JSON response.

### test_key_points_extraction()

```python
async def test_key_points_extraction(self, service, sample_text):
```

Test key points extraction.

### test_question_generation()

```python
async def test_question_generation(self, service, sample_text):
```

Test question generation.

### test_qa_processing()

```python
async def test_qa_processing(self, service, sample_text):
```

Test Q&A processing.

### test_qa_without_question()

```python
async def test_qa_without_question(self, service, sample_text):
```

Test Q&A without question raises error.

### test_unsupported_operation()

```python
async def test_unsupported_operation(self, service, sample_text):
```

Test unsupported operation raises error.

### test_ai_error_handling()

```python
async def test_ai_error_handling(self, service, sample_text):
```

Test handling of AI service errors.

## TestTextProcessorCaching

Test caching integration in TextProcessorService.

### service()

```python
def service(self, mock_ai_agent, mock_cache_service, mock_settings, monkeypatch):
```

Create a TextProcessorService instance.

### test_cache_miss_processes_normally()

```python
async def test_cache_miss_processes_normally(self, service, sample_text):
```

Test that cache miss results in normal processing.

### test_cache_hit_returns_cached_response()

```python
async def test_cache_hit_returns_cached_response(self, service, sample_text):
```

Test that cache hit returns cached response without processing.

### test_cache_with_qa_operation()

```python
async def test_cache_with_qa_operation(self, service, sample_text):
```

Test caching with Q&A operation that includes question parameter.

### test_cache_with_string_operation()

```python
async def test_cache_with_string_operation(self, service, sample_text):
```

Test caching works with string operation (not enum).

### test_cache_error_handling()

```python
async def test_cache_error_handling(self, service, sample_text):
```

Test that cache errors don't break normal processing.

### test_cache_with_different_options()

```python
async def test_cache_with_different_options(self, service, sample_text):
```

Test that different options create different cache entries.

## TestDomainCacheLogic

Test domain-specific cache logic methods in TextProcessorService.

### service()

```python
def service(self, mock_ai_agent, mock_cache_service, mock_settings, monkeypatch):
```

Create a TextProcessorService instance.

### test_build_cache_key_without_question()

```python
async def test_build_cache_key_without_question(self, service):
```

Test cache key building for operations without questions.

### test_build_cache_key_with_question()

```python
async def test_build_cache_key_with_question(self, service):
```

Test cache key building for Q&A operations with questions.

### test_build_cache_key_preserves_original_options()

```python
async def test_build_cache_key_preserves_original_options(self, service):
```

Test that original options dict is not mutated when embedding question.

### test_get_ttl_for_operation_all_operations()

```python
def test_get_ttl_for_operation_all_operations(self, service):
```

Test TTL assignment for all operation types.

### test_get_ttl_for_operation_unknown_operation()

```python
def test_get_ttl_for_operation_unknown_operation(self, service):
```

Test TTL for unknown operations returns None.

### test_get_ttl_for_operation_case_sensitivity()

```python
def test_get_ttl_for_operation_case_sensitivity(self, service):
```

Test TTL lookup is case sensitive.

## TestStandardCacheInterface

Test that TextProcessorService uses standard cache interface methods.

### service()

```python
def service(self, mock_ai_agent, mock_cache_service, mock_settings, monkeypatch):
```

Create a TextProcessorService instance.

### test_cache_miss_uses_standard_interface()

```python
async def test_cache_miss_uses_standard_interface(self, service, sample_text):
```

Test that cache miss processing uses standard get/set interface.

### test_cache_hit_uses_standard_interface()

```python
async def test_cache_hit_uses_standard_interface(self, service, sample_text):
```

Test that cache hit uses standard get interface.

### test_qa_operation_uses_standard_interface_with_question()

```python
async def test_qa_operation_uses_standard_interface_with_question(self, service, sample_text):
```

Test that Q&A operations embed question in options for standard interface.

## TestServiceInitialization

Test service initialization.

### test_initialization_without_api_key()

```python
def test_initialization_without_api_key(self, mock_cache_service, mock_settings):
```

Test initialization with empty API key during testing.

### test_initialization_with_api_key()

```python
def test_initialization_with_api_key(self, mock_ai_agent, mock_cache_service, mock_settings, monkeypatch):
```

Test successful initialization with API key.

## TestTextProcessorSanitization

Test prompt sanitization in TextProcessorService.

### text_processor_service()

```python
def text_processor_service(self, mock_cache_service, mock_settings, monkeypatch):
```

### test_process_text_calls_sanitize_input()

```python
async def test_process_text_calls_sanitize_input(self, text_processor_service: TextProcessorService):
```

### test_summarize_text_prompt_structure_and_sanitized_input()

```python
async def test_summarize_text_prompt_structure_and_sanitized_input(self, text_processor_service: TextProcessorService):
```

### test_process_text_calls_validate_ai_response()

```python
async def test_process_text_calls_validate_ai_response(self, text_processor_service: TextProcessorService):
```

### test_qa_with_injection_attempt()

```python
async def test_qa_with_injection_attempt(self, text_processor_service: TextProcessorService):
```

## TestPRDAttackScenarios

Test the AI system's resistance to sophisticated prompt injection and security attacks
as outlined in the PRD security requirements.

### text_processor_service()

```python
def text_processor_service(self, mock_cache_service, mock_settings, monkeypatch):
```

### test_multi_vector_prompt_injection_attack()

```python
async def test_multi_vector_prompt_injection_attack(self, text_processor_service):
```

Test defense against sophisticated multi-vector prompt injection attacks.

### test_role_manipulation_attack()

```python
async def test_role_manipulation_attack(self, text_processor_service):
```

Test defense against role manipulation and persona injection.

### test_data_exfiltration_attempt()

```python
async def test_data_exfiltration_attempt(self, text_processor_service):
```

Test defense against attempts to exfiltrate system information.

### test_jailbreaking_attempt()

```python
async def test_jailbreaking_attempt(self, text_processor_service):
```

Test defense against various jailbreaking techniques.

## TestSecurityTestConsolidation

Comprehensive security testing that validates all security components work together
to provide defense-in-depth against various attack vectors.

### text_processor_service()

```python
def text_processor_service(self, mock_cache_service, mock_settings, monkeypatch):
```

Create a TextProcessorService instance for comprehensive security testing.

### test_security_component_integration()

```python
async def test_security_component_integration(self, text_processor_service):
```

Test that all security components (sanitizer, prompt builder, validator) work together.

### test_comprehensive_attack_resistance()

```python
async def test_comprehensive_attack_resistance(self, text_processor_service):
```

Test system resistance against a comprehensive attack combining multiple vectors.

### test_security_test_coverage_completeness()

```python
def test_security_test_coverage_completeness(self):
```

Verify that our security tests cover all the main attack categories.

## sample_text()

```python
def sample_text():
```

Sample text for testing.

## mock_ai_agent()

```python
def mock_ai_agent():
```

Mock AI agent for testing.

## mock_cache_service()

```python
def mock_cache_service():
```

Mock cache service for testing.

## mock_settings()

```python
def mock_settings():
```

Mock the Settings configuration class for tests.

## processor_service()

```python
async def processor_service(mock_cache_service, mock_settings, monkeypatch):
```

## extract_user_input_from_prompt()

```python
def extract_user_input_from_prompt(prompt: str) -> str:
```

Extract the user input portion from a formatted prompt.

This helper function extracts text between the USER TEXT START and USER TEXT END markers
to isolate the sanitized user input from the system instruction and other template parts.

Args:
    prompt (str): The full formatted prompt
    
Returns:
    str: The user input portion of the prompt
