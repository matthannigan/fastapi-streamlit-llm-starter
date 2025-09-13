---
sidebar_label: prompt_builder
---

# Prompt building utilities for safely constructing LLM prompts.

  file_path: `backend/app/infrastructure/ai/prompt_builder.py`

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

## escape_user_input()

```python
def escape_user_input(user_input: str) -> str:
```

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
    >>> escape_user_input("Tom & Jerry's "great" adventure")
    "Tom &amp; Jerry&#x27;s &quot;great&quot; adventure"
    
    >>> # Empty input handling
    >>> escape_user_input("")
    ""
    
    >>> # Error handling for invalid input
    >>> escape_user_input(None)
    Traceback (most recent call last):
        ...
    TypeError: user_input must be a string, got <class 'NoneType'>

## create_safe_prompt()

```python
def create_safe_prompt(template_name: str, user_input: str, **kwargs) -> str:
```

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

## get_available_templates()

```python
def get_available_templates() -> list:
```

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
