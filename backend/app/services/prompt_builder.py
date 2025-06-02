"""
Prompt building utilities for safely constructing LLM prompts.

This module provides functions and templates for building structured prompts
with proper escaping and delimiters to prevent injection attacks.
"""

from typing import Dict, Any
from app.utils.prompt_utils import escape_user_input


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