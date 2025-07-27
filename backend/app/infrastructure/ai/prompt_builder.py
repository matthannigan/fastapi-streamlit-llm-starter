"""
Prompt building utilities for safely constructing LLM prompts.

This module provides a comprehensive framework for building structured, secure prompts
for Large Language Model (LLM) interactions. It focuses on preventing prompt injection
attacks while offering flexible templating capabilities for common AI tasks.

Key Features:
    - Safe user input escaping using HTML encoding
    - Pre-built prompt templates for common AI operations
    - Flexible template system with placeholder substitution
    - Injection attack prevention through proper delimiters and escaping
    - Template validation and error handling

Security Considerations:
    All user inputs are automatically escaped to prevent:
    - Prompt injection attacks
    - Template structure manipulation
    - Execution of embedded code or scripts
    - Breaking of prompt delimiters and instructions

Available Templates:
    - 'summarize': Create concise summaries of text content
    - 'sentiment': Analyze sentiment with JSON response format
    - 'key_points': Extract main ideas and important points
    - 'questions': Generate thoughtful questions about content
    - 'question_answer': Answer specific questions based on provided text
    - 'analyze': Perform detailed analysis with structured insights

Main Functions:
    - escape_user_input(): Safely escape user input for prompt embedding
    - create_safe_prompt(): Build prompts from templates with escaped inputs
    - get_available_templates(): List all available prompt templates

Usage Example:
    >>> from app.infrastructure.ai.prompt_builder import create_safe_prompt
    >>> prompt = create_safe_prompt(
    ...     "summarize",
    ...     "User's potentially unsafe <script>content</script>",
    ...     additional_instructions="Keep it under 100 words."
    ... )
    >>> # Returns a safe, properly formatted prompt

Template Structure:
    Templates use clear delimiters and structured sections:
    - <system_instruction>: AI behavior and role definition
    - ---USER TEXT START/END---: Safe boundaries for user content
    - <task_instruction>: Specific task requirements and formatting

Note:
    This module is designed to work with the broader infrastructure framework
    and integrates with caching, monitoring, and resilience components.
"""

from typing import Dict, Any
import html
from typing import Optional


def escape_user_input(user_input: str) -> str:
    """
    Escape user input to make it safe for embedding in prompt templates.
    
    This function uses HTML escaping as the primary mechanism to prevent
    special characters from breaking template structure or being misinterpreted
    by the LLM.
    
    Args:
        user_input (str): The raw user input string to escape.
        
    Returns:
        str: The escaped string safe for use in prompt templates.
        
    Examples:
        >>> escape_user_input("Hello <script>alert('xss')</script>")
        "Hello &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        
        >>> escape_user_input("Tom & Jerry's adventure")
        "Tom &amp; Jerry&#x27;s adventure"
        
        >>> escape_user_input("")
        ""
    """
    if not isinstance(user_input, str):
        raise TypeError(f"user_input must be a string, got {type(user_input)}")
    
    return html.escape(user_input) 


# Template dictionary with structured prompt templates
PROMPT_TEMPLATES: Dict[str, str] = {
    "summarize": """<system_instruction>
You are a helpful AI assistant that specializes in creating concise, accurate summaries. 
Please analyze the following user-provided text and create a clear summary that captures the key points.
</system_instruction>

---USER TEXT START---
{escaped_user_input}
---USER TEXT END---

<task_instruction>
Please provide a summary of the text above. Focus on the main points and keep it concise while preserving important details.
{additional_instructions}
</task_instruction>""",

    "sentiment": """<system_instruction>
Analyze the sentiment of the following text. Respond with a JSON object containing:
- sentiment: "positive", "negative", or "neutral"
- confidence: a number between 0.0 and 1.0
- explanation: a brief explanation of the sentiment
</system_instruction>

---USER TEXT START---
{escaped_user_input}
---USER TEXT END---

<task_instruction>
Response (JSON only):
{additional_instructions}
</task_instruction>""",

    "key_points": """<system_instruction>
You are a helpful AI assistant that extracts the most important key points from text.
Analyze the provided text and identify the key points or main ideas.
</system_instruction>

---USER TEXT START---
{escaped_user_input}
---USER TEXT END---

<task_instruction>
Extract the most important key points from the text above. Return each point as a separate line starting with a dash (-).
{additional_instructions}
</task_instruction>""",

    "questions": """<system_instruction>
You are a helpful AI assistant that generates thoughtful questions about text content.
Create questions that help someone better understand or think more deeply about the content.
</system_instruction>

---USER TEXT START---
{escaped_user_input}
---USER TEXT END---

<task_instruction>
Generate thoughtful questions about the text above. These questions should help someone better understand or think more deeply about the content. Return each question on a separate line.
{additional_instructions}
</task_instruction>""",

    "question_answer": """<system_instruction>
You are a knowledgeable AI assistant that provides accurate and helpful answers to user questions.
Based on the provided text, please answer the given question.
</system_instruction>

---USER TEXT START---
{escaped_user_input}
---USER TEXT END---

---USER QUESTION START---
{user_question}
---USER QUESTION END---

<task_instruction>
Based on the provided text, please answer the given question.
{additional_instructions}
</task_instruction>""",

    "analyze": """<system_instruction>
You are an analytical AI assistant that provides detailed analysis of user-provided content.
Examine the text carefully and provide insights, patterns, and key observations.
</system_instruction>

---USER TEXT START---
{escaped_user_input}
---USER TEXT END---

<task_instruction>
Please analyze the text above and provide:
1. Main themes and concepts
2. Key insights or patterns
3. Important details or observations
{additional_instructions}
</task_instruction>"""
}


def create_safe_prompt(template_name: str, user_input: str, **kwargs) -> str:
    """
    Create a safe prompt by combining a template with escaped user input.
    
    This function retrieves the specified template, escapes the user input to prevent
    injection attacks, and formats the template with the escaped input and additional
    keyword arguments.
    
    Args:
        template_name (str): Name of the template to use (must exist in PROMPT_TEMPLATES)
        user_input (str): Raw user input to be escaped and embedded in the template
        **kwargs: Additional arguments to format into the template
                 For question_answer template, use user_question="question text"
        
    Returns:
        str: Formatted prompt with safely escaped user input
        
    Raises:
        ValueError: If template_name is not found in PROMPT_TEMPLATES
        KeyError: If required template placeholders are missing from kwargs
        
    Examples:
        >>> prompt = create_safe_prompt(
        ...     "summarize", 
        ...     "This is some <script>dangerous</script> text",
        ...     additional_instructions="Keep it under 100 words."
        ... )
        >>> "This is some &lt;script&gt;dangerous&lt;/script&gt; text" in prompt
        True
    """
    # Validate template name
    if template_name not in PROMPT_TEMPLATES:
        available_templates = list(PROMPT_TEMPLATES.keys())
        raise ValueError(
            f"Unknown template name '{template_name}'. "
            f"Available templates: {available_templates}"
        )
    
    # Get the template
    template = PROMPT_TEMPLATES[template_name]
    
    # Escape user input for safety
    escaped_input = escape_user_input(user_input)
    
    # Prepare formatting arguments
    format_args = {
        "escaped_user_input": escaped_input,
        **kwargs
    }
    
    # Set default values for optional placeholders
    if "additional_instructions" not in format_args:
        format_args["additional_instructions"] = ""
    
    # Handle special case for question_answer template
    if template_name == "question_answer" and "user_question" in kwargs:
        # Escape the user question as well for safety
        format_args["user_question"] = escape_user_input(kwargs["user_question"])
    
    try:
        # Format the template with escaped input and additional arguments
        formatted_prompt = template.format(**format_args)
        return formatted_prompt.strip()
    except KeyError as e:
        raise KeyError(
            f"Missing required placeholder {e} for template '{template_name}'. "
            f"Available placeholders in template: {_get_template_placeholders(template)}"
        )


def _get_template_placeholders(template: str) -> list:
    """
    Extract placeholder names from a template string.
    
    Args:
        template (str): Template string with {placeholder} format
        
    Returns:
        list: List of placeholder names found in the template
    """
    import re
    placeholders = re.findall(r'\{(\w+)\}', template)
    return list(set(placeholders))


def get_available_templates() -> list:
    """
    Get list of available template names.
    
    Returns:
        list: List of template names available in PROMPT_TEMPLATES
    """
    return list(PROMPT_TEMPLATES.keys()) 