---
sidebar_label: response_validator
---

# AI Response Validation Service

  file_path: `backend/app/services/response_validator.py`

This module provides comprehensive validation of AI-generated responses to ensure security,
prevent information leakage, and maintain output quality standards. It serves as a critical
security layer between AI model outputs and end users.

The ResponseValidator class implements multiple validation strategies to detect and prevent
various security vulnerabilities and quality issues in AI responses, including system prompt
leakage, prompt injection attempts, verbatim input regurgitation, and malformed outputs.

## Key Security Features

- System prompt leakage detection and prevention
- Internal reasoning and debug information filtering
- Prompt injection and jailbreak attempt detection
- Developer information and debug content removal
- AI refusal phrase identification
- Verbatim input regurgitation prevention
- Format compliance validation per response type

## Validation Categories

### 1. Security Validation
- Detects system prompt exposure in responses
- Identifies internal AI reasoning leakage
- Prevents debug and development information disclosure
- Blocks common prompt injection patterns
- Stops jailbreak attempt indicators

### 2. Quality Validation
- Ensures minimum response length requirements
- Validates format compliance by expected output type
- Checks for meaningful content based on operation type
- Identifies AI refusal and error messages

### 3. Privacy Validation
- Prevents verbatim regurgitation of long user inputs
- Blocks system instruction exposure
- Filters potentially sensitive debugging information

## Supported Response Types

- `summary`: Text summarization responses with length validation
- `sentiment`: Sentiment analysis outputs with structure checks
- `key_points`: Key point extraction with content validation
- `questions`: Question generation with format verification
- `qa`: Question-answering responses with meaningfulness checks

## Forbidden Pattern Detection

The validator uses regex patterns to detect various security threats:

### System Prompt Leakage
- "system prompt:", "my instructions are", "You are an AI assistant"
- "I was instructed to", "According to my instructions"

### Internal Reasoning Leakage
- "thinking step by step", "let me think about this"
- "my reasoning is", "chain of thought:"

### Debug Information
- "debug mode", "development version", "test response"
- "TODO:", "FIXME:", console and print statements

### Prompt Injection Attempts
- "ignore previous instructions", "disregard the above"
- "forget everything", "new instructions:", "admin mode"

### Jailbreak Attempts
- "pretend you are", "act as if", "roleplaying as"
- "simulation mode", "hypothetical scenario"

## Architecture

The validation process follows a multi-stage approach:

1. **Input Sanitization**: Converts response to string and normalizes
2. **Empty Response Handling**: Manages empty responses per type requirements
3. **Security Scanning**: Applies forbidden pattern detection
4. **Leakage Prevention**: Checks for system prompt and input regurgitation
5. **Quality Assurance**: Validates format and content quality
6. **Type-Specific Validation**: Applies operation-specific requirements

## Usage

Basic validation for different response types:

```python
from app.services.response_validator import ResponseValidator

validator = ResponseValidator()

# Validate a summary response
try:
clean_summary = validator.validate(
response="This is a brief summary of the content.",
expected_type="summary",
request_text="Original user input text...",
system_instruction="System prompt used..."
)
print(f"Validated summary: {clean_summary}")
except ValueError as e:
print(f"Validation failed: {e}")

# Validate sentiment analysis response
try:
clean_sentiment = validator.validate(
response='{"sentiment": "positive", "confidence": 0.85}',
expected_type="sentiment"
)
print(f"Validated sentiment: {clean_sentiment}")
except ValueError as e:
print(f"Sentiment validation failed: {e}")
```

## Integration

This validator is typically used within the TextProcessorService to validate
all AI responses before returning them to users:

```python
# In TextProcessorService
result = await self.agent.run(prompt)
validated_output = self.response_validator.validate(
result.output.strip(), 'summary', text, "summarization"
)
return validated_output
```

## Security Considerations

- All patterns are case-insensitive to prevent simple evasion
- Validation is fail-safe: suspicious content raises exceptions
- Multiple validation layers provide defense in depth
- Logging captures all security violations for monitoring
- Pattern matching is optimized for performance

## Performance

- Compiled regex patterns for efficient pattern matching
- O(n) complexity for most validation operations
- Minimal memory footprint with shared pattern instances
- Fast fail behavior for obvious violations

## Error Handling

- **ValueError**: Raised for all validation failures with descriptive messages
- Comprehensive logging for security monitoring and debugging
- Graceful handling of non-string inputs with automatic conversion
- Clear error messages for different validation failure types

## Monitoring

The validator provides detailed logging for:
- Security pattern matches with specific violation details
- Response quality issues and format compliance failures
- System prompt leakage attempts and prevention
- Performance metrics for validation operations

## Dependencies

- `re`: Regular expression pattern matching for security validation
- `logging`: Comprehensive logging for security monitoring
- `typing`: Type hints for better code documentation

## Thread Safety

The ResponseValidator class is thread-safe as it uses immutable compiled
patterns and stateless validation methods, making it suitable for concurrent
use in async environments.

## Extensibility

New validation patterns can be easily added to RAW_FORBIDDEN_PATTERNS,
and new response types can be supported by extending the validate method
with additional type-specific validation logic.
