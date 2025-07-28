# Prompt building utilities for safely constructing LLM prompts.

  file_path: `backend/app/infrastructure/ai/prompt_builder.py`

This module provides a comprehensive framework for building structured, secure prompts
for Large Language Model (LLM) interactions. It focuses on preventing prompt injection
attacks while offering flexible templating capabilities for common AI tasks.

## Key Features

- Safe user input escaping using HTML encoding
- Pre-built prompt templates for common AI operations
- Flexible template system with placeholder substitution
- Injection attack prevention through proper delimiters and escaping
- Template validation and error handling

## Security Considerations

All user inputs are automatically escaped to prevent:
- Prompt injection attacks
- Template structure manipulation
- Execution of embedded code or scripts
- Breaking of prompt delimiters and instructions

## Available Templates

- 'summarize': Create concise summaries of text content
- 'sentiment': Analyze sentiment with JSON response format
- 'key_points': Extract main ideas and important points
- 'questions': Generate thoughtful questions about content
- 'question_answer': Answer specific questions based on provided text
- 'analyze': Perform detailed analysis with structured insights

## Main Functions

- escape_user_input(): Safely escape user input for prompt embedding
- create_safe_prompt(): Build prompts from templates with escaped inputs
- get_available_templates(): List all available prompt templates

## Usage Example

```python
from app.infrastructure.ai.prompt_builder import create_safe_prompt
prompt = create_safe_prompt(
    "summarize",
    "User's potentially unsafe <script>content</script>",
    additional_instructions="Keep it under 100 words."
)
# Returns a safe, properly formatted prompt
```

## Template Structure

Templates use clear delimiters and structured sections:
- <system_instruction>: AI behavior and role definition
- ---USER TEXT START/END---: Safe boundaries for user content
- <task_instruction>: Specific task requirements and formatting

## Note

This module is designed to work with the broader infrastructure framework
and integrates with caching, monitoring, and resilience components.
