"""
Unit tests for prompt_utils module.
"""

import pytest
from app.utils.prompt_utils import escape_user_input


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