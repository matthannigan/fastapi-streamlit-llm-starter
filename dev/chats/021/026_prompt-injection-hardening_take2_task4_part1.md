# Execute task 4
_Exported on 6/1/2025 at 06:31:04 EDT from Cursor (0.50.7)_

---

**User**

Execute Task 4

---

**Cursor**

I'll execute Task 4 by implementing the `create_safe_prompt` function and its supporting infrastructure. Let me start by examining the current state and dependencies.

Let me first check if the dependency (Task 3's `escape_user_input` function) is available:

Great! The `escape_user_input` function is available. Now let me check if the services directory exists and then implement the subtasks:

Perfect! Now I'll start implementing the subtasks. Let me begin with subtask 4.1:

## Subtask 4.1: Create `prompt_builder.py` and Define `PROMPT_TEMPLATES`

```python
"""
Prompt building utilities for safely constructing LLM prompts.

This module provides functions and templates for building structured prompts
with proper escaping and delimiters to prevent injection attacks.
"""

from typing import Dict, Any
from backend.app.utils.prompt_utils import escape_user_input


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
</task_instruction>""",

    "question_answer": """<system_instruction>
You are a knowledgeable AI assistant that provides accurate and helpful answers to user questions.
Base your response on the provided context when available.
</system_instruction>

---USER TEXT START---
{escaped_user_input}
---USER TEXT END---

<task_instruction>
Please answer the question or respond to the request above. If context is provided, base your answer on that context.
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
```

Now let me update the subtask status and move to creating comprehensive unit tests:

Great! Now subtasks 4.2 and 4.3 are actually already implemented as part of the complete function. Let me mark them as done and create the unit tests for subtask 4.4:

Now let me check if the tests directory structure exists:

I need to create the services test directory:

Now let me create comprehensive unit tests for the prompt builder:

```python
"""
Unit tests for the prompt_builder module.

This module tests the create_safe_prompt function and related utilities
to ensure proper escaping, template formatting, and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.prompt_builder import (
    create_safe_prompt,
    PROMPT_TEMPLATES,
    get_available_templates,
    _get_template_placeholders
)


class TestCreateSafePrompt:
    """Test cases for the create_safe_prompt function."""

    def test_create_safe_prompt_with_summarize_template(self):
        """Test basic functionality with summarize template."""
        user_input = "This is a test document that needs summarizing."
        additional_instructions = "Keep it under 50 words."
        
        result = create_safe_prompt(
            "summarize", 
            user_input, 
            additional_instructions=additional_instructions
        )
        
        # Check that the result contains all expected components
        assert "<system_instruction>" in result
        assert "---USER TEXT START---" in result
        assert "---USER TEXT END---" in result
        assert "<task_instruction>" in result
        assert user_input in result  # Should be unescaped since no special chars
        assert additional_instructions in result

    def test_create_safe_prompt_with_special_characters(self):
        """Test that special characters in user input are properly escaped."""
        user_input = "Test with <script>alert('xss')</script> and & symbols"
        
        result = create_safe_prompt("summarize", user_input)
        
        # Check that dangerous characters are escaped
        assert "&lt;script&gt;" in result
        assert "alert(&#x27;xss&#x27;)" in result
        assert "&lt;/script&gt;" in result
        assert "&amp;" in result
        # Original dangerous content should not be present
        assert "<script>" not in result
        assert "alert('xss')" not in result

    @patch('backend.app.services.prompt_builder.escape_user_input')
    def test_escape_user_input_is_called(self, mock_escape):
        """Test that escape_user_input is called with the user input."""
        mock_escape.return_value = "escaped_input"
        user_input = "test input"
        
        create_safe_prompt("summarize", user_input)
        
        mock_escape.assert_called_once_with(user_input)

    def test_create_safe_prompt_with_analyze_template(self):
        """Test functionality with analyze template."""
        user_input = "Data to analyze: sales figures, customer feedback"
        
        result = create_safe_prompt("analyze", user_input)
        
        assert "analytical AI assistant" in result
        assert "1. Main themes and concepts" in result
        assert "2. Key insights or patterns" in result
        assert "3. Important details" in result
        assert user_input in result

    def test_create_safe_prompt_with_question_answer_template(self):
        """Test functionality with question_answer template."""
        user_input = "What is the capital of France?"
        
        result = create_safe_prompt("question_answer", user_input)
        
        assert "knowledgeable AI assistant" in result
        assert "Please answer the question" in result
        assert user_input in result

    def test_create_safe_prompt_with_additional_kwargs(self):
        """Test that additional kwargs are properly formatted into template."""
        user_input = "Test content"
        custom_instructions = "Be very detailed in your response."
        
        result = create_safe_prompt(
            "summarize", 
            user_input,
            additional_instructions=custom_instructions
        )
        
        assert custom_instructions in result

    def test_create_safe_prompt_with_empty_additional_instructions(self):
        """Test that missing additional_instructions defaults to empty string."""
        user_input = "Test content"
        
        result = create_safe_prompt("summarize", user_input)
        
        # Should not contain placeholder
        assert "{additional_instructions}" not in result
        # Function should complete successfully
        assert len(result) > 0

    def test_create_safe_prompt_invalid_template_name(self):
        """Test that ValueError is raised for invalid template names."""
        with pytest.raises(ValueError) as exc_info:
            create_safe_prompt("nonexistent_template", "test input")
        
        assert "Unknown template name 'nonexistent_template'" in str(exc_info.value)
        assert "Available templates:" in str(exc_info.value)

    def test_create_safe_prompt_missing_required_placeholder(self):
        """Test error handling for missing required placeholders."""
        # Create a custom template with a required placeholder for testing
        original_templates = PROMPT_TEMPLATES.copy()
        PROMPT_TEMPLATES["test_template"] = "Hello {required_field}!"
        
        try:
            with pytest.raises(KeyError) as exc_info:
                create_safe_prompt("test_template", "test input")
            
            assert "Missing required placeholder" in str(exc_info.value)
            assert "required_field" in str(exc_info.value)
        finally:
            # Restore original templates
            PROMPT_TEMPLATES.clear()
            PROMPT_TEMPLATES.update(original_templates)

    def test_create_safe_prompt_empty_user_input(self):
        """Test handling of empty user input."""
        result = create_safe_prompt("summarize", "")
        
        assert "---USER TEXT START---" in result
        assert "---USER TEXT END---" in result
        # Should handle empty input gracefully
        assert len(result) > 0

    def test_create_safe_prompt_whitespace_user_input(self):
        """Test handling of whitespace-only user input."""
        user_input = "   \n\t   "
        result = create_safe_prompt("summarize", user_input)
        
        assert user_input in result
        assert len(result) > 0

    def test_create_safe_prompt_unicode_characters(self):
        """Test handling of unicode characters in user input."""
        user_input = "Testing unicode: 🚀 测试 café naïve résumé"
        result = create_safe_prompt("summarize", user_input)
        
        assert user_input in result
        assert len(result) > 0

    def test_create_safe_prompt_delimiters_present(self):
        """Test that delimiters are correctly placed in all templates."""
        user_input = "Test content"
        
        for template_name in PROMPT_TEMPLATES.keys():
            result = create_safe_prompt(template_name, user_input)
            
            assert "---USER TEXT START---" in result
            assert "---USER TEXT END---" in result
            # User content should be between delimiters
            start_pos = result.find("---USER TEXT START---")
            end_pos = result.find("---USER TEXT END---")
            assert start_pos < end_pos
            user_content_section = result[start_pos:end_pos + len("---USER TEXT END---")]
            assert user_input in user_content_section


class TestPromptTemplates:
    """Test cases for PROMPT_TEMPLATES and related utilities."""

    def test_prompt_templates_structure(self):
        """Test that all templates have required structure."""
        required_elements = [
            "<system_instruction>",
            "</system_instruction>",
            "---USER TEXT START---",
            "{escaped_user_input}",
            "---USER TEXT END---",
            "<task_instruction>",
            "</task_instruction>"
        ]
        
        for template_name, template in PROMPT_TEMPLATES.items():
            for element in required_elements:
                assert element in template, f"Template '{template_name}' missing '{element}'"

    def test_get_available_templates(self):
        """Test get_available_templates function."""
        templates = get_available_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert "summarize" in templates
        assert "analyze" in templates
        assert "question_answer" in templates

    def test_get_template_placeholders(self):
        """Test _get_template_placeholders function."""
        template = "Hello {name}, your {item} is ready. Cost: {price}"
        placeholders = _get_template_placeholders(template)
        
        assert isinstance(placeholders, list)
        assert set(placeholders) == {"name", "item", "price"}

    def test_get_template_placeholders_empty(self):
        """Test _get_template_placeholders with no placeholders."""
        template = "Hello world, no placeholders here!"
        placeholders = _get_template_placeholders(template)
        
        assert placeholders == []

    def test_get_template_placeholders_duplicate(self):
        """Test that duplicate placeholders are handled correctly."""
        template = "Hello {name}, {name} is your name. Your {item} costs {item} dollars."
        placeholders = _get_template_placeholders(template)
        
        # Should return unique placeholders only
        assert set(placeholders) == {"name", "item"}
        assert len(placeholders) == 2


class TestIntegrationWithEscapeUserInput:
    """Integration tests to verify proper interaction with escape_user_input."""

    def test_integration_with_actual_escape_function(self):
        """Test that the actual escape_user_input function is properly integrated."""
        dangerous_input = "Hello <script>alert('test')</script> & some text"
        
        result = create_safe_prompt("summarize", dangerous_input)
        
        # Verify escaping occurred
        assert "&lt;script&gt;" in result
        assert "&amp;" in result
        assert "<script>" not in result

    def test_html_entities_preserved(self):
        """Test that pre-existing HTML entities are handled correctly."""
        input_with_entities = "Price: $100 &amp; tax &lt; $20"
        
        result = create_safe_prompt("summarize", input_with_entities)
        
        # The escape function should handle pre-existing entities
        assert len(result) > 0
        assert input_with_entities in result or "&amp;amp;" in result  # Double-escaping may occur


# Integration test with mock to verify call patterns
class TestErrorHandlingIntegration:
    """Test error handling and edge cases in integration scenarios."""

    def test_template_formatting_robustness(self):
        """Test that template formatting is robust against various inputs."""
        test_cases = [
            "",  # Empty string
            " ",  # Single space
            "\n",  # Newline
            "\t",  # Tab
            "Normal text",  # Regular text
            "Text with {braces}",  # Text with braces
            "Text with \\ backslashes",  # Backslashes
            "Text with % percent signs",  # Percent signs
        ]
        
        for test_input in test_cases:
            result = create_safe_prompt("summarize", test_input)
            assert len(result) > 0
            assert "---USER TEXT START---" in result
            assert "---USER TEXT END---" in result

    def test_all_templates_work_with_complex_input(self):
        """Test that all templates work with complex, potentially problematic input."""
        complex_input = """
        Multi-line input with:
        - Special chars: <>&"'
        - Unicode: 🚀 café
        - Code: function() { return "test"; }
        - Numbers: 123.45
        - Symbols: @#$%^&*()
        """
        
        for template_name in PROMPT_TEMPLATES.keys():
            result = create_safe_prompt(template_name, complex_input)
            assert len(result) > 0
            assert "---USER TEXT START---" in result
            assert "---USER TEXT END---" in result
            # Verify no template formatting errors
            assert "{" not in result or "escaped_user_input" not in result
```

Now let me create an `__init__.py` file for the services tests directory:

```python
"""Tests for services module."""
```

Now let me run the tests to ensure everything is working correctly:

I need to use the backend's virtual environment. Let me check how to activate it:

I need to fix the import path. Let me check the test structure and fix the imports:

I can see that imports use `app.` directly. Let me fix the test imports:

```python
"""
Unit tests for the prompt_builder module.

This module tests the create_safe_prompt function and related utilities
to ensure proper escaping, template formatting, and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.prompt_builder import (
    create_safe_prompt,
    PROMPT_TEMPLATES,
    get_available_templates,
    _get_template_placeholders
)

// ... existing code ...
```

Now I also need to fix the mock patch import:

```python
    @patch('app.services.prompt_builder.escape_user_input')
    def test_escape_user_input_is_called(self, mock_escape):
```

Now let me run the tests again:

Now I need to fix the import in the prompt_builder.py file itself:

```python
"""
Prompt building utilities for safely constructing LLM prompts.

This module provides functions and templates for building structured prompts
with proper escaping and delimiters to prevent injection attacks.
"""

from typing import Dict, Any
from app.utils.prompt_utils import escape_user_input

// ... existing code ...
```

Now let me run the tests again:

Excellent! All tests are passing. Now let me update the subtask status and complete the task:

Now let me mark the main task as complete:

Let me also run a quick integration test to make sure the function works as expected:

Perfect! Let me update the task file to document the completed implementation:

## Task 4 Implementation Summary

✅ **TASK 4 COMPLETED SUCCESSFULLY**

I have successfully executed Task 4: "Develop `create_safe_prompt` Function in `prompt_builder.py` Leveraging Existing Delimiter Strategy". Here's what was accomplished:

### 📁 **Files Created:**
1. **`backend/app/services/prompt_builder.py`** - Main implementation
2. **`backend/tests/services/test_prompt_builder.py`** - Comprehensive test suite
3. **`backend/tests/services/__init__.py`** - Test package initialization

### 🛠️ **Core Implementation:**

**`create_safe_prompt` Function:**
- **Signature:** `create_safe_prompt(template_name: str, user_input: str, **kwargs) -> str`
- **Integration:** Successfully calls `escape_user_input` from Task 3 dependency
- **Error Handling:** Validates template names, handles missing placeholders
- **Flexibility:** Supports custom kwargs and defaults for optional parameters

**Template System:**
- **Three templates implemented:** `summarize`, `analyze`, `question_answer`
- **Delimiter Strategy:** All templates use `---USER TEXT START---`/`---USER TEXT END---` delimiters
- **Structure:** Proper separation of system instructions, user content, and task instructions
- **Safety:** User content is properly escaped before template insertion

### 🧪 **Testing:**
- **22 comprehensive test cases** covering:
  - Basic functionality with all templates
  - Special character escaping verification  
  - Error handling (invalid templates, missing placeholders)
  - Edge cases (empty input, unicode, whitespace)
  - Integration with `escape_user_input` function
  - Template structure validation

- **All tests pass** ✅ (22/22 successful)

### 🔒 **Security Features:**
- **Input Escaping:** Dangerous content like `<script>alert('xss')</script>` properly escaped to `&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;`
- **Delimiter Protection:** User content safely contained within delimiters
- **Template Validation:** Prevents injection through invalid template names
- **Error Safety:** Graceful error handling with informative messages

### 📋 **All Subtasks Completed:**
- ✅ **4.1:** Created `prompt_builder.py` and defined `PROMPT_TEMPLATES`
- ✅ **4.2:** Implemented `create_safe_prompt` function logic
- ✅ **4.3:** Integrated `escape_user_input` call
- ✅ **4.4:** Added comprehensive error handling and unit tests

The implementation successfully leverages the existing delimiter strategy from the existing codebase while providing a robust, safe, and well-tested prompt building system. The function is ready for integration with the text processing pipeline and provides a solid foundation for secure prompt construction.

