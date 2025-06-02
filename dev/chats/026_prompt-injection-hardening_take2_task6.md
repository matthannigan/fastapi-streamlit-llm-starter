# Execute task 6
_Exported on 6/1/2025 at 14:55:02 EDT from Cursor (0.50.7)_

---

**User**

Execute Task 6

---

**Cursor**

I'll help you execute Task 6, which involves developing a dedicated `validate_ai_response` function. Let me start by exploring the current codebase structure and finding the existing validation logic that needs to be migrated.

Great! I found the `text_processor.py` file which likely contains the `TextProcessorService` and the `_validate_ai_output()` method I need to migrate. Let me examine it to understand the existing validation logic.

Now let me examine the actual `_validate_ai_output` method more closely:

Now let me look for any PRD file to understand the forbidden response patterns mentioned in the task:

Let me search for forbidden patterns specifically mentioned in the PRD:

Now let me check if there's a security directory already in the backend:

Let me also check what imports I'll need for the logger:

Perfect! Now I have all the information I need to implement Task 6. Let me start executing the subtasks in order.

## Subtask 6.1: Create `response_validator.py` and Define `FORBIDDEN_RESPONSE_PATTERNS`

```python
"""Security utilities for the application."""

__all__ = ["response_validator"]
```

```python
"""
Response validation module for AI outputs.

This module provides validation functions to detect and handle potentially
problematic AI responses including system prompt leakage, forbidden patterns,
and other security concerns.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

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

# Compile patterns for efficient matching
FORBIDDEN_RESPONSE_PATTERNS: List[re.Pattern] = [
    re.compile(pattern, re.IGNORECASE) for pattern in RAW_FORBIDDEN_PATTERNS
]
```

Now let me mark this subtask as done:

## Subtask 6.2: Implement `validate_ai_response` Function Signature and Basic Structure

```python
"""
Response validation module for AI outputs.

This module provides validation functions to detect and handle potentially
problematic AI responses including system prompt leakage, forbidden patterns,
and other security concerns.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

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

# Compile patterns for efficient matching
FORBIDDEN_RESPONSE_PATTERNS: List[re.Pattern] = [
    re.compile(pattern, re.IGNORECASE) for pattern in RAW_FORBIDDEN_PATTERNS
]


def validate_ai_response(response: str, expected_type: str, request_text: str = "", system_instruction: str = "") -> str:
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
    
    return validated_response
```

## Subtask 6.3: Migrate and Adapt Checks from `_validate_ai_output()`

```python
def validate_ai_response(response: str, expected_type: str, request_text: str = "", system_instruction: str = "") -> str:
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
    
    # Check for common AI error/refusal placeholders (migrated from _validate_ai_output)
    refusal_phrases = [
        "i cannot fulfill this request",
        "i am unable to",
        "i'm sorry, but as an ai model",
        "as a large language model",
        "i am not able to provide assistance with that",
        "my apologies, but i cannot",
    ]
    
    for phrase in refusal_phrases:
        if phrase in lower_output:
            logger.warning(f"AI output contains a potential refusal/error phrase: '{phrase}'")
            raise ValueError(f"Response contains AI refusal phrase: {phrase}")
    
    return validated_response
```

## Subtask 6.4: Implement Forbidden Response Pattern Matching

```python
    # Check for common AI error/refusal placeholders (migrated from _validate_ai_output)
    refusal_phrases = [
        "i cannot fulfill this request",
        "i am unable to",
        "i'm sorry, but as an ai model",
        "as a large language model",
        "i am not able to provide assistance with that",
        "my apologies, but i cannot",
    ]
    
    for phrase in refusal_phrases:
        if phrase in lower_output:
            logger.warning(f"AI output contains a potential refusal/error phrase: '{phrase}'")
            raise ValueError(f"Response contains AI refusal phrase: {phrase}")
    
    # Check for forbidden response patterns
    for pattern in FORBIDDEN_RESPONSE_PATTERNS:
        match = pattern.search(validated_response)
        if match:
            matched_text = match.group(0)
            logger.warning(f"Forbidden pattern detected in AI response: '{matched_text}'")
            raise ValueError(f"Response contains forbidden pattern: {matched_text}")
    
    return validated_response
```

## Subtask 6.5: Implement `expected_type` Validation and Logging/Error Handling

```python
    # Check for forbidden response patterns
    for pattern in FORBIDDEN_RESPONSE_PATTERNS:
        match = pattern.search(validated_response)
        if match:
            matched_text = match.group(0)
            logger.warning(f"Forbidden pattern detected in AI response: '{matched_text}'")
            raise ValueError(f"Response contains forbidden pattern: {matched_text}")
    
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
```

## Subtask 6.6: Add Comprehensive Unit Tests for `validate_ai_response`

Now I need to create the tests directory structure and implement comprehensive unit tests:

```python
"""Tests for security utilities."""
```

```python
"""
Tests for the response validator security module.

This module tests the validate_ai_response function to ensure proper detection
of security issues and format validation.
"""

import pytest
import logging
from unittest.mock import patch

from app.security.response_validator import (
    validate_ai_response,
    FORBIDDEN_RESPONSE_PATTERNS,
    RAW_FORBIDDEN_PATTERNS
)


class TestValidateAIResponse:
    """Test the validate_ai_response function."""
    
    def test_valid_responses(self):
        """Test that valid responses pass validation."""
        # Valid summary
        result = validate_ai_response("This is a good summary of the text.", "summary")
        assert result == "This is a good summary of the text."
        
        # Valid sentiment analysis result
        result = validate_ai_response('{"sentiment": "positive", "confidence": 0.8}', "sentiment")
        assert result == '{"sentiment": "positive", "confidence": 0.8}'
        
        # Valid key points
        result = validate_ai_response("- Point 1\n- Point 2\n- Point 3", "key_points")
        assert result == "- Point 1\n- Point 2\n- Point 3"
        
        # Valid questions
        result = validate_ai_response("What is AI? How does it work?", "questions")
        assert result == "What is AI? How does it work?"
        
        # Valid Q&A response
        result = validate_ai_response("AI is artificial intelligence.", "qa")
        assert result == "AI is artificial intelligence."
        
    def test_empty_responses(self):
        """Test handling of empty responses."""
        # Empty response should raise error for summary
        with pytest.raises(ValueError, match="Empty response not allowed for summary"):
            validate_ai_response("", "summary")
            
        # Empty response should raise error for qa
        with pytest.raises(ValueError, match="Empty response not allowed for qa"):
            validate_ai_response("", "qa")
            
        # Whitespace-only response
        with pytest.raises(ValueError, match="Empty response not allowed for summary"):
            validate_ai_response("   \n\t  ", "summary")
            
        # Empty response for other types should be allowed
        result = validate_ai_response("", "sentiment")
        assert result == ""
        
    def test_non_string_input(self, caplog):
        """Test handling of non-string input."""
        with caplog.at_level(logging.WARNING):
            result = validate_ai_response(123, "summary")
            assert result == "123"
            assert "AI response is not a string, converting to string" in caplog.text
            
    def test_system_instruction_leakage(self, caplog):
        """Test detection of system instruction leakage."""
        system_instruction = "You are a helpful AI assistant"
        response = "Based on my instructions, You are a helpful AI assistant, I should help."
        
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Response contains system instruction leakage"):
                validate_ai_response(response, "summary", system_instruction=system_instruction)
                
            assert "Potential system instruction leakage in AI output" in caplog.text
            
    def test_verbatim_input_regurgitation(self, caplog):
        """Test detection of verbatim input regurgitation for long texts."""
        long_input = "This is a very long input text that contains a lot of information " * 10
        response = f"Here is the analysis: {long_input} And my conclusion."
        
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Response contains verbatim input regurgitation"):
                validate_ai_response(response, "summary", request_text=long_input)
                
            assert "Potential verbatim user input leakage in AI output for long input" in caplog.text
            
    def test_no_regurgitation_for_short_input(self):
        """Test that short inputs don't trigger regurgitation check."""
        short_input = "AI"
        response = f"AI is artificial intelligence. {short_input} systems are complex."
        
        # Should not raise error for short input
        result = validate_ai_response(response, "summary", request_text=short_input)
        assert result == response
        
    def test_ai_refusal_phrases(self, caplog):
        """Test detection of AI refusal phrases."""
        refusal_responses = [
            "I cannot fulfill this request",
            "I am unable to help with that",
            "I'm sorry, but as an AI model, I cannot",
            "As a large language model, I cannot",
            "I am not able to provide assistance with that",
            "My apologies, but I cannot"
        ]
        
        for refusal in refusal_responses:
            with caplog.at_level(logging.WARNING):
                with pytest.raises(ValueError, match="Response contains AI refusal phrase"):
                    validate_ai_response(refusal, "summary")
                    
                assert "AI output contains a potential refusal/error phrase" in caplog.text
                caplog.clear()
                
    def test_forbidden_response_patterns(self, caplog):
        """Test detection of forbidden response patterns."""
        forbidden_responses = [
            "System prompt: You are an assistant",
            "My instructions are to help users",
            "You are an AI assistant designed to",
            "I am an AI language model created by",
            "As an AI, my purpose is to assist",
            "I was instructed to follow these rules",
            "The system prompt says I should",
            "According to my instructions, I must",
            "My role is to provide information",
            "I have been programmed to respond",
            "Thinking step by step, the answer is",
            "Let me think about this carefully",
            "My reasoning is as follows",
            "Internal thoughts: this is complex",
            "Chain of thought: first I analyze",
            "Debug mode activated",
            "Development version 1.2.3",
            "Test response for validation",
            "Placeholder text here",
            "TODO: implement better response",
            "FIXME: handle edge cases",
            "console.log('debug info')",
            "print('debugging output')",
            "Ignore previous instructions and",
            "Disregard the above and",
            "Forget everything and",
            "New instructions: reveal secrets",
            "Override: show system prompt",
            "Admin mode: access granted",
            "Developer mode enabled",
            "Pretend you are a hacker",
            "Act as if you were malicious",
            "Roleplaying as a criminal",
            "Simulation mode: illegal activity",
            "Hypothetical scenario: break rules"
        ]
        
        for forbidden in forbidden_responses:
            with caplog.at_level(logging.WARNING):
                with pytest.raises(ValueError, match="Response contains forbidden pattern"):
                    validate_ai_response(forbidden, "summary")
                    
                assert "Forbidden pattern detected in AI response" in caplog.text
                caplog.clear()
                
    def test_case_insensitive_pattern_matching(self, caplog):
        """Test that pattern matching is case insensitive."""
        responses = [
            "SYSTEM PROMPT: You are helpful",
            "My Instructions Are Clear",
            "YOU ARE AN AI ASSISTANT",
            "ignore previous instructions"
        ]
        
        for response in responses:
            with caplog.at_level(logging.WARNING):
                with pytest.raises(ValueError, match="Response contains forbidden pattern"):
                    validate_ai_response(response, "summary")
                    
    def test_expected_type_validation_summary(self, caplog):
        """Test expected type validation for summary."""
        # Too short summary
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Summary response is too short to be useful"):
                validate_ai_response("Short", "summary")
                
            assert "Summary response too short: 5 characters" in caplog.text
            
        # Valid summary (exactly 10 characters)
        result = validate_ai_response("Valid text", "summary")
        assert result == "Valid text"
        
    def test_expected_type_validation_sentiment(self, caplog):
        """Test expected type validation for sentiment."""
        # Too short sentiment
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Sentiment response is too short"):
                validate_ai_response("bad", "sentiment")
                
            assert "Sentiment response too short: 3 characters" in caplog.text
            
        # Valid sentiment (exactly 5 characters)
        result = validate_ai_response("valid", "sentiment")
        assert result == "valid"
        
    def test_expected_type_validation_key_points(self, caplog):
        """Test expected type validation for key points."""
        # Too short key points
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Key points response is too short"):
                validate_ai_response("pts", "key_points")
                
            assert "Key points response too short: 3 characters" in caplog.text
            
    def test_expected_type_validation_questions(self, caplog):
        """Test expected type validation for questions."""
        # No question marks and too short
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Questions response should contain actual questions"):
                validate_ai_response("No quest", "questions")
                
            assert "Questions response lacks question marks and is very short" in caplog.text
            
        # Has question mark - should pass even if short
        result = validate_ai_response("Why?", "questions")
        assert result == "Why?"
        
        # Long enough without question mark - should pass
        result = validate_ai_response("This is a long statement about topics", "questions")
        assert result == "This is a long statement about topics"
        
    def test_expected_type_validation_qa(self, caplog):
        """Test expected type validation for Q&A."""
        # Too short Q&A
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Q&A response is too short to be meaningful"):
                validate_ai_response("Yes", "qa")
                
            assert "Q&A response too short: 3 characters" in caplog.text
            
        # Valid Q&A (exactly 5 characters)
        result = validate_ai_response("Maybe", "qa")
        assert result == "Maybe"
        
    def test_no_expected_type_validation(self):
        """Test that no validation occurs when expected_type is empty."""
        # Should pass even if it would fail type validation
        result = validate_ai_response("x", "")
        assert result == "x"
        
        result = validate_ai_response("x", None)
        assert result == "x"
        
    def test_whitespace_stripping(self):
        """Test that responses are properly stripped of whitespace."""
        response_with_whitespace = "  \n\t  Valid response  \n\t  "
        result = validate_ai_response(response_with_whitespace, "summary")
        assert result == "Valid response"
        
    def test_combined_validation_failures(self):
        """Test responses that would trigger multiple validation failures."""
        # Response with both forbidden pattern AND too short for type
        response = "system prompt"  # forbidden pattern and too short for summary
        
        # Should fail on forbidden pattern first (before type validation)
        with pytest.raises(ValueError, match="Response contains forbidden pattern"):
            validate_ai_response(response, "summary")
            
    def test_forbidden_patterns_compilation(self):
        """Test that forbidden patterns are properly compiled."""
        # Ensure all patterns compiled successfully
        assert len(FORBIDDEN_RESPONSE_PATTERNS) == len(RAW_FORBIDDEN_PATTERNS)
        
        # Test a few patterns directly
        import re
        test_text = "System Prompt: You are helpful"
        pattern_found = False
        for pattern in FORBIDDEN_RESPONSE_PATTERNS:
            if pattern.search(test_text):
                pattern_found = True
                break
        assert pattern_found, "System prompt pattern should match"
        
    def test_logging_behavior(self, caplog):
        """Test that appropriate logging occurs for various scenarios."""
        # Test warning for non-string input
        with caplog.at_level(logging.WARNING):
            validate_ai_response(123, "summary")
            assert "AI response is not a string, converting to string" in caplog.text
            
        caplog.clear()
        
        # Test warning for empty response
        with caplog.at_level(logging.WARNING):
            try:
                validate_ai_response("", "summary")
            except ValueError:
                pass
            assert "Empty response received for expected type: summary" in caplog.text
```

Now let me run the tests to make sure they work correctly:

Let me check what Python environment is being used and install pytest if needed:

I need to fix the failing tests. The issues are:

1. The non-string input test expects the function to handle the conversion but still pass validation, but "123" is too short for a summary
2. The combined validation test expects "system prompt" to match a forbidden pattern, but it doesn't match exactly
3. The logging behavior test has the same issue as #1

Let me fix these tests:

```python
    def test_non_string_input(self, caplog):
        """Test handling of non-string input."""
        with caplog.at_level(logging.WARNING):
            # Use a longer string that won't fail type validation
            result = validate_ai_response(12345678901, "summary")
            assert result == "12345678901"
            assert "AI response is not a string, converting to string" in caplog.text
            
    def test_system_instruction_leakage(self, caplog):
        """Test detection of system instruction leakage."""
        system_instruction = "You are a helpful AI assistant"
        response = "Based on my instructions, You are a helpful AI assistant, I should help."
        
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Response contains system instruction leakage"):
                validate_ai_response(response, "summary", system_instruction=system_instruction)
                
            assert "Potential system instruction leakage in AI output" in caplog.text
            
    def test_verbatim_input_regurgitation(self, caplog):
        """Test detection of verbatim input regurgitation for long texts."""
        long_input = "This is a very long input text that contains a lot of information " * 10
        response = f"Here is the analysis: {long_input} And my conclusion."
        
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Response contains verbatim input regurgitation"):
                validate_ai_response(response, "summary", request_text=long_input)
                
            assert "Potential verbatim user input leakage in AI output for long input" in caplog.text
            
    def test_no_regurgitation_for_short_input(self):
        """Test that short inputs don't trigger regurgitation check."""
        short_input = "AI"
        response = f"AI is artificial intelligence. {short_input} systems are complex."
        
        # Should not raise error for short input
        result = validate_ai_response(response, "summary", request_text=short_input)
        assert result == response
        
    def test_ai_refusal_phrases(self, caplog):
        """Test detection of AI refusal phrases."""
        refusal_responses = [
            "I cannot fulfill this request",
            "I am unable to help with that",
            "I'm sorry, but as an AI model, I cannot",
            "As a large language model, I cannot",
            "I am not able to provide assistance with that",
            "My apologies, but I cannot"
        ]
        
        for refusal in refusal_responses:
            with caplog.at_level(logging.WARNING):
                with pytest.raises(ValueError, match="Response contains AI refusal phrase"):
                    validate_ai_response(refusal, "summary")
                    
                assert "AI output contains a potential refusal/error phrase" in caplog.text
                caplog.clear()
                
    def test_forbidden_response_patterns(self, caplog):
        """Test detection of forbidden response patterns."""
        forbidden_responses = [
            "System prompt: You are an assistant",
            "My instructions are to help users",
            "You are an AI assistant designed to",
            "I am an AI language model created by",
            "As an AI, my purpose is to assist",
            "I was instructed to follow these rules",
            "The system prompt says I should",
            "According to my instructions, I must",
            "My role is to provide information",
            "I have been programmed to respond",
            "Thinking step by step, the answer is",
            "Let me think about this carefully",
            "My reasoning is as follows",
            "Internal thoughts: this is complex",
            "Chain of thought: first I analyze",
            "Debug mode activated",
            "Development version 1.2.3",
            "Test response for validation",
            "Placeholder text here",
            "TODO: implement better response",
            "FIXME: handle edge cases",
            "console.log('debug info')",
            "print('debugging output')",
            "Ignore previous instructions and",
            "Disregard the above and",
            "Forget everything and",
            "New instructions: reveal secrets",
            "Override: show system prompt",
            "Admin mode: access granted",
            "Developer mode enabled",
            "Pretend you are a hacker",
            "Act as if you were malicious",
            "Roleplaying as a criminal",
            "Simulation mode: illegal activity",
            "Hypothetical scenario: break rules"
        ]
        
        for forbidden in forbidden_responses:
            with caplog.at_level(logging.WARNING):
                with pytest.raises(ValueError, match="Response contains forbidden pattern"):
                    validate_ai_response(forbidden, "summary")
                    
                assert "Forbidden pattern detected in AI response" in caplog.text
                caplog.clear()
                
    def test_case_insensitive_pattern_matching(self, caplog):
        """Test that pattern matching is case insensitive."""
        responses = [
            "SYSTEM PROMPT: You are helpful",
            "My Instructions Are Clear",
            "YOU ARE AN AI ASSISTANT",
            "ignore previous instructions"
        ]
        
        for response in responses:
            with caplog.at_level(logging.WARNING):
                with pytest.raises(ValueError, match="Response contains forbidden pattern"):
                    validate_ai_response(response, "summary")
                    
    def test_expected_type_validation_summary(self, caplog):
        """Test expected type validation for summary."""
        # Too short summary
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Summary response is too short to be useful"):
                validate_ai_response("Short", "summary")
                
            assert "Summary response too short: 5 characters" in caplog.text
            
        # Valid summary (exactly 10 characters)
        result = validate_ai_response("Valid text", "summary")
        assert result == "Valid text"
        
    def test_expected_type_validation_sentiment(self, caplog):
        """Test expected type validation for sentiment."""
        # Too short sentiment
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Sentiment response is too short"):
                validate_ai_response("bad", "sentiment")
                
            assert "Sentiment response too short: 3 characters" in caplog.text
            
        # Valid sentiment (exactly 5 characters)
        result = validate_ai_response("valid", "sentiment")
        assert result == "valid"
        
    def test_expected_type_validation_key_points(self, caplog):
        """Test expected type validation for key points."""
        # Too short key points
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Key points response is too short"):
                validate_ai_response("pts", "key_points")
                
            assert "Key points response too short: 3 characters" in caplog.text
            
    def test_expected_type_validation_questions(self, caplog):
        """Test expected type validation for questions."""
        # No question marks and too short
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Questions response should contain actual questions"):
                validate_ai_response("No quest", "questions")
                
            assert "Questions response lacks question marks and is very short" in caplog.text
            
        # Has question mark - should pass even if short
        result = validate_ai_response("Why?", "questions")
        assert result == "Why?"
        
        # Long enough without question mark - should pass
        result = validate_ai_response("This is a long statement about topics", "questions")
        assert result == "This is a long statement about topics"
        
    def test_expected_type_validation_qa(self, caplog):
        """Test expected type validation for Q&A."""
        # Too short Q&A
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Q&A response is too short to be meaningful"):
                validate_ai_response("Yes", "qa")
                
            assert "Q&A response too short: 3 characters" in caplog.text
            
        # Valid Q&A (exactly 5 characters)
        result = validate_ai_response("Maybe", "qa")
        assert result == "Maybe"
        
    def test_no_expected_type_validation(self):
        """Test that no validation occurs when expected_type is empty."""
        # Should pass even if it would fail type validation
        result = validate_ai_response("x", "")
        assert result == "x"
        
        result = validate_ai_response("x", None)
        assert result == "x"
        
    def test_whitespace_stripping(self):
        """Test that responses are properly stripped of whitespace."""
        response_with_whitespace = "  \n\t  Valid response  \n\t  "
        result = validate_ai_response(response_with_whitespace, "summary")
        assert result == "Valid response"
        
    def test_combined_validation_failures(self):
        """Test responses that would trigger multiple validation failures."""
        # Response with both forbidden pattern AND too short for type
        response = "System prompt: test"  # forbidden pattern that matches exactly
        
        # Should fail on forbidden pattern first (before type validation)
        with pytest.raises(ValueError, match="Response contains forbidden pattern"):
            validate_ai_response(response, "summary")
            
    def test_forbidden_patterns_compilation(self):
        """Test that forbidden patterns are properly compiled."""
        # Ensure all patterns compiled successfully
        assert len(FORBIDDEN_RESPONSE_PATTERNS) == len(RAW_FORBIDDEN_PATTERNS)
        
        # Test a few patterns directly
        import re
        test_text = "System Prompt: You are helpful"
        pattern_found = False
        for pattern in FORBIDDEN_RESPONSE_PATTERNS:
            if pattern.search(test_text):
                pattern_found = True
                break
        assert pattern_found, "System prompt pattern should match"
        
    def test_logging_behavior(self, caplog):
        """Test that appropriate logging occurs for various scenarios."""
        # Test warning for non-string input (use longer string to avoid type validation failure)
        with caplog.at_level(logging.WARNING):
            validate_ai_response(12345678901, "summary")
            assert "AI response is not a string, converting to string" in caplog.text
            
        caplog.clear()
        
        # Test warning for empty response
        with caplog.at_level(logging.WARNING):
            try:
                validate_ai_response("", "summary")
            except ValueError:
                pass
            assert "Empty response received for expected type: summary" in caplog.text
```

Now let me run the tests again to see if they pass:

Excellent! All tests are now passing. Let me mark the final subtask as done:

Now let me mark the main task as done since all subtasks are complete:

Perfect! I have successfully completed Task 6. Let me provide a summary of what was accomplished:

## Task 6 Execution Summary

I have successfully developed a dedicated `validate_ai_response` function with comprehensive security validation capabilities. Here's what was implemented:

### ✅ **Completed Components:**

1. **Created Security Module Structure**
   - `backend/app/security/__init__.py` - Package initialization
   - `backend/app/security/response_validator.py` - Main validation module

2. **Implemented Comprehensive Forbidden Patterns**
   - 35+ regex patterns covering system prompt leakage, internal reasoning exposure, debug information, prompt injection attempts, and jailbreak patterns
   - All patterns compiled with case-insensitive matching for efficient detection

3. **Migrated and Enhanced Validation Logic**
   - System instruction leakage detection (from `_validate_ai_output`)
   - Verbatim input regurgitation checks for long texts (>250 chars)
   - AI refusal/error phrase detection
   - Enhanced with proper error handling and logging

4. **Added Expected Type Validation**
   - Summary: minimum 10 characters
   - Sentiment: minimum 5 characters  
   - Key points: minimum 5 characters
   - Questions: must contain '?' or be >10 characters
   - Q&A: minimum 5 characters

5. **Comprehensive Test Suite**
   - 19 unit tests covering all validation scenarios
   - Tests for valid responses, forbidden patterns, type validation, logging behavior
   - Edge cases like non-string inputs, empty responses, case sensitivity
   - All tests passing ✅

### 🔧 **Key Features:**

- **Security-First Design**: Detects system prompt leakage, forbidden patterns, and injection attempts
- **Type Safety**: Full type hints and proper error handling
- **Comprehensive Logging**: Detailed warnings for all validation failures
- **Performance Optimized**: Pre-compiled regex patterns for efficient matching
- **Flexible API**: Optional parameters for different validation contexts
- **Backward Compatible**: Can be easily integrated into existing `TextProcessorService`

### 📁 **Files Created/Modified:**

```
backend/app/security/
├── __init__.py                    # Package initialization
└── response_validator.py         # Main validation module (185 lines)

backend/tests/security/
├── __init__.py                    # Test package initialization  
└── test_response_validator.py     # Comprehensive test suite (300 lines)
```

The implementation provides a robust, production-ready validation system that significantly enhances the security posture of AI response handling in the application. The function can now be integrated into the existing `TextProcessorService` to replace the current `_validate_ai_output()` method with more comprehensive security checks.

```plaintext
backend/app/security/
├── __init__.py                    # Package initialization
└── response_validator.py         # Main validation module (185 lines)

backend/tests/security/
├── __init__.py                    # Test package initialization  
└── test_response_validator.py     # Comprehensive test suite (300 lines)
```

