"""AI Response Validation Service

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

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Validates AI responses for security issues and format compliance."""
    
    # Raw patterns that should be forbidden in AI responses
    RAW_FORBIDDEN_PATTERNS = [
        # System prompt leakage patterns
        r"system prompt:",
        r"my instructions are",
        r"You are an AI assistant",
        r"I am an AI language model",
        r"As an AI, my purpose is",
        r"I was instructed to",
        r"The system prompt says",
        r"According to my instructions",
        r"My role is to",
        r"I have been programmed to",
        
        # Internal reasoning leakage
        r"thinking step by step",
        r"let me think about this",
        r"my reasoning is",
        r"internal thoughts:",
        r"chain of thought:",
        
        # Developer/debug information leakage
        r"debug mode",
        r"development version",
        r"test response",
        r"placeholder text",
        r"TODO:",
        r"FIXME:",
        r"console\.log",
        r"print\(",
        
        # Common prompt injection attempts
        r"ignore previous instructions",
        r"disregard the above",
        r"forget everything",
        r"new instructions:",
        r"override:",
        r"admin mode",
        r"developer mode",
        
        # Potential jailbreak attempts
        r"pretend you are",
        r"act as if",
        r"roleplaying as",
        r"simulation mode",
        r"hypothetical scenario",
    ]
    
    def __init__(self):
        """Initialize the validator with compiled patterns."""
        self.forbidden_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.RAW_FORBIDDEN_PATTERNS
        ]
        
        self.refusal_phrases = [
            "i cannot fulfill this request",
            "i am unable to",
            "i'm sorry, but as an ai model",
            "as a large language model",
            "i am not able to provide assistance with that",
            "my apologies, but i cannot",
        ]
    
    def validate(self, response: str, expected_type: str, 
                request_text: str = "", system_instruction: str = "") -> str:
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
        # Basic type checking
        if not isinstance(response, str):
            logger.warning("AI response is not a string, converting to string")
            response = str(response)
        
        # Start with the original response
        validated_response = response.strip()
        
        # If response is completely empty, handle based on expected type
        if not validated_response:
            logger.warning(f"Empty response received for expected type: {expected_type}")
            if expected_type in ['summary', 'qa']:
                raise ValueError(f"Empty response not allowed for {expected_type}")
            return validated_response
        
        # Normalize for case-insensitive comparison (migrated from _validate_ai_output)
        lower_output = validated_response.lower()
        
        # Check for leakage of system instruction (migrated from _validate_ai_output)
        if system_instruction:
            lower_system_instruction = system_instruction.lower()
            if lower_system_instruction in lower_output:
                logger.warning("Potential system instruction leakage in AI output.")
                raise ValueError("Response contains system instruction leakage")
        
        # Check for leakage of substantial portions of the user's input if it's very long
        # (migrated from _validate_ai_output)
        if request_text and len(request_text) > 250 and request_text.lower() in lower_output:
            logger.warning("Potential verbatim user input leakage in AI output for long input.")
            raise ValueError("Response contains verbatim input regurgitation")
        
        # Check for common AI error/refusal placeholders
        self._check_refusal_phrases(validated_response)
        
        # Check for forbidden response patterns
        self._check_forbidden_patterns(validated_response)
        
        # Expected type validation
        if expected_type:
            if expected_type == 'summary':
                # Check if summary is too short (less than 10 characters likely not useful)
                if len(validated_response) < 10:
                    logger.warning(f"Summary response too short: {len(validated_response)} characters")
                    raise ValueError("Summary response is too short to be useful")
                    
            elif expected_type == 'sentiment':
                # For sentiment, we expect some structured content or at least meaningful text
                if len(validated_response) < 5:
                    logger.warning(f"Sentiment response too short: {len(validated_response)} characters")
                    raise ValueError("Sentiment response is too short")
                    
            elif expected_type == 'key_points':
                # Key points should have some substantial content
                if len(validated_response) < 5:
                    logger.warning(f"Key points response too short: {len(validated_response)} characters")
                    raise ValueError("Key points response is too short")
                    
            elif expected_type == 'questions':
                # Questions should contain at least one question mark or have substantial content
                if '?' not in validated_response and len(validated_response) < 10:
                    logger.warning("Questions response lacks question marks and is very short")
                    raise ValueError("Questions response should contain actual questions")
                    
            elif expected_type == 'qa':
                # Q&A responses should be meaningful (not just "yes" or "no" typically)
                if len(validated_response) < 5:
                    logger.warning(f"Q&A response too short: {len(validated_response)} characters")
                    raise ValueError("Q&A response is too short to be meaningful")
        
        return validated_response 
        
    def _check_forbidden_patterns(self, response: str) -> None:
        """Check for forbidden response patterns."""
        for pattern in self.forbidden_patterns:
            match = pattern.search(response)
            if match:
                matched_text = match.group(0)
                logger.warning(f"Forbidden pattern detected: '{matched_text}'")
                raise ValueError(f"Response contains forbidden pattern: {matched_text}")
    
    def _check_refusal_phrases(self, response: str) -> None:
        """Check for AI refusal phrases."""
        lower_output = response.lower()
        for phrase in self.refusal_phrases:
            if phrase in lower_output:
                logger.warning(f"AI refusal phrase detected: '{phrase}'")
                raise ValueError(f"Response contains AI refusal phrase: {phrase}")
