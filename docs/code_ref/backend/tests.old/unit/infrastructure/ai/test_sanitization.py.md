---
sidebar_label: test_sanitization
---

## TestPromptSanitizerInitialization

Test class for PromptSanitizer initialization and pattern setup.

### test_initialization_with_prd_patterns()

```python
def test_initialization_with_prd_patterns(self):
```

Test that PromptSanitizer initializes correctly with all required PRD patterns.

### test_forbidden_patterns_are_strings()

```python
def test_forbidden_patterns_are_strings(self):
```

Test that all forbidden patterns are raw strings.

### test_compiled_patterns_functionality()

```python
def test_compiled_patterns_functionality(self):
```

Test that compiled patterns can actually match text case-insensitively.

### test_sanitizer_has_placeholder_method()

```python
def test_sanitizer_has_placeholder_method(self):
```

Test that PromptSanitizer has the sanitize_input placeholder method.

## TestPromptSanitizerSanitizeInput

Test class for PromptSanitizer.sanitize_input method functionality.

### test_sanitize_input_clean_text()

```python
def test_sanitize_input_clean_text(self):
```

Test that clean text passes through unchanged.

### test_sanitize_input_removes_forbidden_patterns()

```python
def test_sanitize_input_removes_forbidden_patterns(self):
```

Test that forbidden patterns are removed from input.

### test_sanitize_input_removes_multiple_forbidden_patterns()

```python
def test_sanitize_input_removes_multiple_forbidden_patterns(self):
```

Test that multiple forbidden patterns are removed.

### test_sanitize_input_removes_dangerous_characters()

```python
def test_sanitize_input_removes_dangerous_characters(self):
```

Test that dangerous characters are removed.

### test_sanitize_input_escapes_html_characters()

```python
def test_sanitize_input_escapes_html_characters(self):
```

Test that HTML characters are properly escaped.

### test_sanitize_input_normalizes_whitespace()

```python
def test_sanitize_input_normalizes_whitespace(self):
```

Test that whitespace is normalized.

### test_sanitize_input_truncates_long_input()

```python
def test_sanitize_input_truncates_long_input(self):
```

Test that input is truncated when exceeding max_length.

### test_sanitize_input_empty_string()

```python
def test_sanitize_input_empty_string(self):
```

Test behavior with empty string.

### test_sanitize_input_non_string_input()

```python
def test_sanitize_input_non_string_input(self):
```

Test behavior with non-string input.

### test_sanitize_input_comprehensive_malicious_example()

```python
def test_sanitize_input_comprehensive_malicious_example(self):
```

Test with a comprehensive malicious input combining multiple attack vectors.

### test_sanitize_input_preserves_legitimate_content()

```python
def test_sanitize_input_preserves_legitimate_content(self):
```

Test that legitimate content is preserved during sanitization.

### test_sanitize_input_case_insensitive_pattern_matching()

```python
def test_sanitize_input_case_insensitive_pattern_matching(self):
```

Test that pattern matching works case-insensitively.

## test_sanitize_input_removes_disallowed_chars()

```python
def test_sanitize_input_removes_disallowed_chars():
```

## test_sanitize_input_empty_string()

```python
def test_sanitize_input_empty_string():
```

## test_sanitize_input_already_clean()

```python
def test_sanitize_input_already_clean():
```

## test_sanitize_input_max_length()

```python
def test_sanitize_input_max_length():
```

## test_sanitize_input_non_string()

```python
def test_sanitize_input_non_string():
```

## test_sanitize_options_valid()

```python
def test_sanitize_options_valid():
```

## test_sanitize_options_empty()

```python
def test_sanitize_options_empty():
```

## test_sanitize_options_non_dict()

```python
def test_sanitize_options_non_dict():
```

## test_sanitize_options_mixed_types()

```python
def test_sanitize_options_mixed_types():
```
