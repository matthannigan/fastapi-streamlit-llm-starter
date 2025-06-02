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