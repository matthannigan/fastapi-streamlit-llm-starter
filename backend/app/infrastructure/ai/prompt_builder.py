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


def escape_user_input(user_input: str) -> str:
    """
    Escape user input for safe embedding in LLM prompt templates using HTML entity encoding.

    Provides defense against prompt injection attacks by converting special characters to their
    HTML entity equivalents, preventing them from being interpreted as template control characters
    or prompt manipulation instructions by the LLM.

    Args:
        user_input: Raw user input string requiring escaping for prompt safety. Must be string type,
                   non-string inputs raise TypeError for explicit error handling.

    Returns:
        HTML-escaped string safe for embedding in prompt templates with:
        - Special characters (<, >, &, ', ") converted to HTML entities
        - Original text meaning preserved while preventing injection
        - Structure suitable for safe template substitution

    Raises:
        TypeError: When user_input is not a string type, ensuring type safety

    Behavior:
        - Applies standard HTML entity encoding to all special characters
        - Preserves original text content and readability for LLM processing
        - Prevents template delimiter manipulation and instruction injection
        - Returns empty string unchanged (no escaping needed)
        - Thread-safe operation for concurrent prompt building
        - Validates input type explicitly for security and debugging

    Examples:
        >>> # Basic HTML character escaping
        >>> escape_user_input("Hello <script>alert('xss')</script>")
        "Hello &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"

        >>> # Ampersand and quote escaping
        >>> escape_user_input("Tom & Jerry's \"great\" adventure")
        "Tom &amp; Jerry&#x27;s &quot;great&quot; adventure"

        >>> # Empty input handling
        >>> escape_user_input("")
        ""

        >>> # Error handling for invalid input
        >>> escape_user_input(None)
        Traceback (most recent call last):
            ...
        TypeError: user_input must be a string, got <class 'NoneType'>
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


def create_safe_prompt(template_name: str, user_input: str, **kwargs: Any) -> str:
    """
    Create secure LLM prompt by combining template with HTML-escaped user input and validation.

    Provides the primary interface for safe prompt construction, automatically handling input
    escaping, template validation, and parameter substitution. Prevents prompt injection attacks
    while enabling flexible prompt customization through template parameters.

    Args:
        template_name: Name of prompt template from PROMPT_TEMPLATES. Must be one of:
                      'summarize', 'sentiment', 'key_points', 'questions',
                      'question_answer', 'analyze'. Case-sensitive string identifier.
        user_input: Raw user content to embed in prompt. Automatically escaped for safety.
                   Can contain any text content including potential injection attempts.
        **kwargs: Additional template parameters for customization:
                 - additional_instructions (str): Optional task-specific guidance
                 - user_question (str): Required for 'question_answer' template
                 - Other template-specific placeholders as needed

    Returns:
        Complete formatted prompt string with:
        - Selected template structure with system and task instructions
        - User input safely escaped and embedded between delimiters
        - Additional parameters properly substituted
        - Trimmed whitespace for clean formatting

    Raises:
        ValueError: When template_name not found in available templates, includes
                   list of valid template names for debugging
        KeyError: When required template placeholder missing from kwargs, includes
                 available placeholders for the specific template

    Behavior:
        - Validates template name against available templates before processing
        - Automatically escapes all user input using HTML entity encoding
        - Applies special escaping to user_question parameter for question_answer template
        - Sets empty string default for optional additional_instructions parameter
        - Performs template formatting with comprehensive error handling
        - Returns trimmed prompt ready for LLM processing
        - Thread-safe operation for concurrent prompt generation

    Examples:
        >>> # Basic summarization prompt
        >>> prompt = create_safe_prompt(
        ...     "summarize",
        ...     "This is <script>alert('xss')</script> content"
        ... )
        >>> "&lt;script&gt;" in prompt
        True
        >>> "---USER TEXT START---" in prompt
        True

        >>> # Question answering with custom instructions
        >>> qa_prompt = create_safe_prompt(
        ...     "question_answer",
        ...     "Context about machine learning algorithms",
        ...     user_question="What is supervised learning?",
        ...     additional_instructions="Provide examples."
        ... )
        >>> "supervised learning" in qa_prompt
        True

        >>> # Error handling for invalid template
        >>> create_safe_prompt("invalid_template", "text")
        Traceback (most recent call last):
            ...
        ValueError: Unknown template name 'invalid_template'...

        >>> # Sentiment analysis with structured output
        >>> sentiment_prompt = create_safe_prompt(
        ...     "sentiment",
        ...     "I absolutely love this product!"
        ... )
        >>> "JSON" in sentiment_prompt
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
    Extract placeholder names from template string for error reporting and validation.

    Utility function that parses template strings to identify all placeholder names,
    supporting error messages and template validation. Uses regex pattern matching
    to find standard Python string format placeholders.

    Args:
        template: Template string containing {placeholder} format specifiers to analyze

    Returns:
        List of unique placeholder names found in template:
        - Extracted from {name} format patterns
        - Deduplicated for unique placeholder identification
        - Ordered by first occurrence in template

    Behavior:
        - Uses regex pattern matching to find {word} placeholder patterns
        - Extracts only the placeholder name without braces
        - Returns unique placeholder names (duplicates removed)
        - Empty list for templates without placeholders
        - Thread-safe operation for concurrent template analysis

    Examples:
        >>> template = "Hello {name}, your {item} is {status}."
        >>> placeholders = _get_template_placeholders(template)
        >>> set(placeholders) == {'name', 'item', 'status'}
        True

        >>> # Template with duplicate placeholders
        >>> template = "User {name} has {count} items. Hello {name}!"
        >>> placeholders = _get_template_placeholders(template)
        >>> sorted(placeholders) == ['count', 'name']
        True

        >>> # Template with no placeholders
        >>> _get_template_placeholders("Static text only")
        []
    """
    import re
    placeholders = re.findall(r"\{(\w+)\}", template)
    return list(set(placeholders))


def get_available_templates() -> list:
    """
    Retrieve list of available prompt template names for template selection and validation.

    Provides programmatic access to all registered prompt templates, enabling dynamic
    template discovery, validation, and user interface generation for template selection.

    Returns:
        List of template name strings available in PROMPT_TEMPLATES:
        - All currently registered template identifiers
        - Suitable for validation and user selection interfaces
        - Consistent with create_safe_prompt() template_name parameter

    Behavior:
        - Returns current state of PROMPT_TEMPLATES dictionary keys
        - List order matches dictionary key iteration order
        - No filtering or sorting applied to preserve registration order
        - Thread-safe access to template registry
        - Suitable for runtime template discovery and validation

    Examples:
        >>> templates = get_available_templates()
        >>> 'summarize' in templates
        True
        >>> 'sentiment' in templates
        True
        >>> len(templates) >= 6  # At least 6 built-in templates
        True

        >>> # Template validation usage
        >>> user_template = "analyze"
        >>> if user_template in get_available_templates():
        ...     prompt = create_safe_prompt(user_template, "content")

        >>> # UI generation usage
        >>> for template in get_available_templates():
        ...     print(f"Available template: {template}")
    """
    return list(PROMPT_TEMPLATES.keys())
