# This file correctly tests app.infrastructure.ai.prompt_builder infrastructure modules
# and mostly conforms to Infrastructure Test criteria with high coverage, business-agnostic
# abstractions, isolation with mocking, and comprehensive template testing.

"""
Unit tests for the prompt_builder module.

This module tests the create_safe_prompt function and related utilities
to ensure proper escaping, template formatting, and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.infrastructure.ai.prompt_builder import (
    create_safe_prompt,
    PROMPT_TEMPLATES,
    get_available_templates,
    _get_template_placeholders,
    escape_user_input
)

class TestEscapeUserInput:
    """Test cases for the escape_user_input function."""

    def test_escape_basic_html_characters(self):
        """Test escaping of basic HTML special characters."""
        # Test < and >
        result = escape_user_input("Hello <world>")
        assert result == "Hello &lt;world&gt;"
        
        # Test &
        result = escape_user_input("Tom & Jerry")
        assert result == "Tom &amp; Jerry"
        
        # Test quotes
        result = escape_user_input('Say "hello" to the world')
        assert result == "Say &quot;hello&quot; to the world"
        
        result = escape_user_input("Tom's adventure")
        assert result == "Tom&#x27;s adventure"

    def test_escape_script_tags(self):
        """Test escaping of potentially dangerous script tags."""
        dangerous_input = "<script>alert('xss')</script>"
        result = escape_user_input(dangerous_input)
        expected = "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        assert result == expected

    def test_escape_complex_html(self):
        """Test escaping of complex HTML structures."""
        html_input = '<div class="test" onclick="alert(&quot;click&quot;)">Content</div>'
        result = escape_user_input(html_input)
        expected = "&lt;div class=&quot;test&quot; onclick=&quot;alert(&amp;quot;click&amp;quot;)&quot;&gt;Content&lt;/div&gt;"
        assert result == expected

    def test_empty_string(self):
        """Test escaping of empty string."""
        result = escape_user_input("")
        assert result == ""

    def test_string_without_special_characters(self):
        """Test that normal strings pass through unchanged."""
        normal_input = "Hello world 123 abc"
        result = escape_user_input(normal_input)
        assert result == normal_input

    def test_already_escaped_string(self):
        """Test behavior with already escaped content."""
        # This tests what happens when we escape already escaped content
        pre_escaped = "&lt;script&gt;"
        result = escape_user_input(pre_escaped)
        # html.escape will escape the & again
        expected = "&amp;lt;script&amp;gt;"
        assert result == expected

    def test_unicode_characters(self):
        """Test that unicode characters are preserved."""
        unicode_input = "Hello 世界 🌍 café"
        result = escape_user_input(unicode_input)
        assert result == unicode_input

    def test_mixed_content(self):
        """Test escaping of mixed content with various special characters."""
        mixed_input = "User said: <b>\"Hello & goodbye\"</b> at 3:00PM"
        result = escape_user_input(mixed_input)
        expected = "User said: &lt;b&gt;&quot;Hello &amp; goodbye&quot;&lt;/b&gt; at 3:00PM"
        assert result == expected

    def test_newlines_and_whitespace(self):
        """Test that newlines and whitespace are preserved."""
        input_with_newlines = "Line 1\nLine 2\t\tTabbed\r\nWindows newline"
        result = escape_user_input(input_with_newlines)
        assert result == input_with_newlines

    def test_type_error_for_non_string(self):
        """Test that TypeError is raised for non-string input."""
        with pytest.raises(TypeError, match="user_input must be a string"):
            escape_user_input(123)
        
        with pytest.raises(TypeError, match="user_input must be a string"):
            escape_user_input(None)
        
        with pytest.raises(TypeError, match="user_input must be a string"):
            escape_user_input(["list", "input"])

    def test_edge_cases(self):
        """Test various edge cases."""
        # Very long string
        long_string = "a" * 10000 + "<script>" + "b" * 10000
        result = escape_user_input(long_string)
        assert "&lt;script&gt;" in result
        assert len(result) > len(long_string)  # Should be longer due to escaping
        
        # String with only special characters
        special_only = "<>&\"'"
        result = escape_user_input(special_only)
        assert result == "&lt;&gt;&amp;&quot;&#x27;"

    def test_function_is_idempotent_for_safe_content(self):
        """Test that the function is idempotent for content without special chars."""
        safe_input = "This is a safe string with no special characters"
        result1 = escape_user_input(safe_input)
        result2 = escape_user_input(result1)
        assert result1 == result2 == safe_input 


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

    @patch('app.infrastructure.ai.prompt_builder.escape_user_input')
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
        user_input = "Paris is the capital of France. It's a beautiful city with many monuments."
        user_question = "What is the capital of France?"
        
        result = create_safe_prompt("question_answer", user_input, user_question=user_question)
        
        assert "knowledgeable AI assistant" in result
        assert "Based on the provided text, please answer the given question" in result
        # Check for escaped version since input should be HTML-escaped
        assert "Paris is the capital of France. It&#x27;s a beautiful city with many monuments." in result
        assert user_question in result
        assert "---USER QUESTION START---" in result
        assert "---USER QUESTION END---" in result

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
            # Handle question_answer template which requires user_question parameter
            if template_name == "question_answer":
                result = create_safe_prompt(template_name, user_input, user_question="What is this about?")
            else:
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
            # Handle question_answer template which requires user_question parameter
            if template_name == "question_answer":
                result = create_safe_prompt(template_name, complex_input, user_question="What is this complex input about?")
            else:
                result = create_safe_prompt(template_name, complex_input)
            assert len(result) > 0
            assert "---USER TEXT START---" in result
            assert "---USER TEXT END---" in result
            # Verify no template formatting errors
            assert "{" not in result or "escaped_user_input" not in result 