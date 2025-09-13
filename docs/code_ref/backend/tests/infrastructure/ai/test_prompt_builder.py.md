---
sidebar_label: test_prompt_builder
---

# Unit tests for the prompt_builder module.

  file_path: `backend/tests/infrastructure/ai/test_prompt_builder.py`

This module tests the create_safe_prompt function and related utilities
to ensure proper escaping, template formatting, and error handling.

## TestEscapeUserInput

Test cases for the escape_user_input function.

### test_escape_basic_html_characters()

```python
def test_escape_basic_html_characters(self):
```

Test escaping of basic HTML special characters.

### test_escape_script_tags()

```python
def test_escape_script_tags(self):
```

Test escaping of potentially dangerous script tags.

### test_escape_complex_html()

```python
def test_escape_complex_html(self):
```

Test escaping of complex HTML structures.

### test_empty_string()

```python
def test_empty_string(self):
```

Test escaping of empty string.

### test_string_without_special_characters()

```python
def test_string_without_special_characters(self):
```

Test that normal strings pass through unchanged.

### test_already_escaped_string()

```python
def test_already_escaped_string(self):
```

Test behavior with already escaped content.

### test_unicode_characters()

```python
def test_unicode_characters(self):
```

Test that unicode characters are preserved.

### test_mixed_content()

```python
def test_mixed_content(self):
```

Test escaping of mixed content with various special characters.

### test_newlines_and_whitespace()

```python
def test_newlines_and_whitespace(self):
```

Test that newlines and whitespace are preserved.

### test_type_error_for_non_string()

```python
def test_type_error_for_non_string(self):
```

Test that TypeError is raised for non-string input.

### test_edge_cases()

```python
def test_edge_cases(self):
```

Test various edge cases.

### test_function_is_idempotent_for_safe_content()

```python
def test_function_is_idempotent_for_safe_content(self):
```

Test that the function is idempotent for content without special chars.

## TestCreateSafePrompt

Test cases for the create_safe_prompt function.

### test_create_safe_prompt_with_summarize_template()

```python
def test_create_safe_prompt_with_summarize_template(self):
```

Test basic functionality with summarize template.

### test_create_safe_prompt_with_special_characters()

```python
def test_create_safe_prompt_with_special_characters(self):
```

Test that special characters in user input are properly escaped.

### test_escape_user_input_is_called()

```python
def test_escape_user_input_is_called(self, mock_escape):
```

Test that escape_user_input is called with the user input.

### test_create_safe_prompt_with_analyze_template()

```python
def test_create_safe_prompt_with_analyze_template(self):
```

Test functionality with analyze template.

### test_create_safe_prompt_with_question_answer_template()

```python
def test_create_safe_prompt_with_question_answer_template(self):
```

Test functionality with question_answer template.

### test_create_safe_prompt_with_additional_kwargs()

```python
def test_create_safe_prompt_with_additional_kwargs(self):
```

Test that additional kwargs are properly formatted into template.

### test_create_safe_prompt_with_empty_additional_instructions()

```python
def test_create_safe_prompt_with_empty_additional_instructions(self):
```

Test that missing additional_instructions defaults to empty string.

### test_create_safe_prompt_invalid_template_name()

```python
def test_create_safe_prompt_invalid_template_name(self):
```

Test that ValueError is raised for invalid template names.

### test_create_safe_prompt_missing_required_placeholder()

```python
def test_create_safe_prompt_missing_required_placeholder(self):
```

Test error handling for missing required placeholders.

### test_create_safe_prompt_empty_user_input()

```python
def test_create_safe_prompt_empty_user_input(self):
```

Test handling of empty user input.

### test_create_safe_prompt_whitespace_user_input()

```python
def test_create_safe_prompt_whitespace_user_input(self):
```

Test handling of whitespace-only user input.

### test_create_safe_prompt_unicode_characters()

```python
def test_create_safe_prompt_unicode_characters(self):
```

Test handling of unicode characters in user input.

### test_create_safe_prompt_delimiters_present()

```python
def test_create_safe_prompt_delimiters_present(self):
```

Test that delimiters are correctly placed in all templates.

## TestPromptTemplates

Test cases for PROMPT_TEMPLATES and related utilities.

### test_prompt_templates_structure()

```python
def test_prompt_templates_structure(self):
```

Test that all templates have required structure.

### test_get_available_templates()

```python
def test_get_available_templates(self):
```

Test get_available_templates function.

### test_get_template_placeholders()

```python
def test_get_template_placeholders(self):
```

Test _get_template_placeholders function.

### test_get_template_placeholders_empty()

```python
def test_get_template_placeholders_empty(self):
```

Test _get_template_placeholders with no placeholders.

### test_get_template_placeholders_duplicate()

```python
def test_get_template_placeholders_duplicate(self):
```

Test that duplicate placeholders are handled correctly.

## TestIntegrationWithEscapeUserInput

Integration tests to verify proper interaction with escape_user_input.

### test_integration_with_actual_escape_function()

```python
def test_integration_with_actual_escape_function(self):
```

Test that the actual escape_user_input function is properly integrated.

### test_html_entities_preserved()

```python
def test_html_entities_preserved(self):
```

Test that pre-existing HTML entities are handled correctly.

## TestErrorHandlingIntegration

Test error handling and edge cases in integration scenarios.

### test_template_formatting_robustness()

```python
def test_template_formatting_robustness(self):
```

Test that template formatting is robust against various inputs.

### test_all_templates_work_with_complex_input()

```python
def test_all_templates_work_with_complex_input(self):
```

Test that all templates work with complex, potentially problematic input.
