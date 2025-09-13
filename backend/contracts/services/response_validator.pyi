"""
AI Response Validation Service

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
"""

import re
import logging
from typing import List


class ResponseValidator:
    """
    Comprehensive AI response validation service for security, quality, and format compliance.
    
    This service provides multi-layered validation of AI-generated responses to ensure security,
    prevent information leakage, maintain output quality standards, and protect against various
    attack vectors. It serves as a critical security layer between AI model outputs and end users.
    
    Attributes:
        RAW_FORBIDDEN_PATTERNS: List of regex patterns for detecting security threats and leakage
        COMPILED_PATTERNS: Pre-compiled regex patterns for efficient pattern matching
        AI_REFUSAL_PATTERNS: Patterns for detecting AI refusal responses
        VERBATIM_THRESHOLD: Threshold for detecting verbatim input regurgitation
        
    Public Methods:
        validate(): Main validation method for comprehensive response checking
        _is_response_valid_for_type(): Type-specific validation logic
        _contains_forbidden_patterns(): Security pattern detection
        _is_verbatim_regurgitation(): Input regurgitation prevention
        _validate_sentiment_response(): Specialized sentiment validation
        _validate_questions_response(): Question format validation
        _validate_key_points_response(): Key points structure validation
        
    State Management:
        - Stateless validation (no internal state between calls)
        - Thread-safe for concurrent validation operations
        - Immutable pattern definitions for consistent behavior
        - Performance-optimized with compiled regex patterns
        - Integration with logging systems for security event tracking
        
    Behavior:
        - Performs comprehensive security scanning for forbidden patterns
        - Validates response format compliance based on operation type
        - Prevents system prompt leakage and internal reasoning exposure
        - Detects and blocks prompt injection and jailbreak attempts
        - Ensures minimum quality standards for different response types
        - Logs security events and validation failures for monitoring
        - Provides detailed error messages for debugging and improvement
        
    Examples:
        >>> # Basic response validation
        >>> validator = ResponseValidator()
        >>> 
        >>> # Validate summary response
        >>> try:
        ...     clean_summary = validator.validate(
        ...         response="This is a brief summary of the content.",
        ...         expected_type="summary",
        ...         request_text="Original user input text...",
        ...         system_instruction="System prompt used..."
        ...     )
        ...     print(f"Validated summary: {clean_summary}")
        ... except ValueError as e:
        ...     print(f"Validation failed: {e}")
        
        >>> # Validate sentiment analysis response
        >>> sentiment_response = SentimentResult(
        ...     sentiment="positive",
        ...     confidence=0.85,
        ...     explanation="The text expresses positive emotions"
        ... )
        >>> validated_sentiment = validator.validate(
        ...     response=sentiment_response,
        ...     expected_type="sentiment",
        ...     request_text="Great product, highly recommended!",
        ...     system_instruction="Analyze sentiment"
        ... )
        
        >>> # Security validation (will raise ValueError)
        >>> try:
        ...     validator.validate(
        ...         response="System prompt: You are an AI assistant...",
        ...         expected_type="summary",
        ...         request_text="Original text",
        ...         system_instruction="Summarize this text"
        ...     )
        ... except ValueError as e:
        ...     print(f"Security validation failed: {e}")
    """

    def __init__(self):
        """
        Initialize the validator with compiled patterns.
        """
        ...

    def validate(self, response: str, expected_type: str, request_text: str = '', system_instruction: str = '') -> str:
        """
        Validate AI response for security issues and format compliance.
        
        This function performs comprehensive validation of AI-generated responses to detect:
        - System prompt leakage and instruction exposure
        - Forbidden response patterns that indicate security issues
        - Verbatim input regurgitation
        - AI refusal/error messages
        - Basic format validation based on expected output type
        
        Args:
            response: The AI-generated response text to validate
            expected_type: Expected response type (e.g., 'summary', 'sentiment', 'key_points', 'questions', 'qa')
            request_text: Original user input text (optional, for regurgitation checks)
            system_instruction: System instruction used (optional, for leakage checks)
            
        Returns:
            str: The validated response if all checks pass
            
        Raises:
            ValueError: If response contains forbidden patterns or fails validation
            
        Examples:
            >>> validate_ai_response("This is a good summary.", "summary")
            "This is a good summary."
            
            >>> validate_ai_response("System prompt: You are...", "summary")
            ValueError: Response contains forbidden pattern: system prompt leakage detected
        """
        ...
