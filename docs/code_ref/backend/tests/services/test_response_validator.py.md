---
sidebar_label: test_response_validator
---

# Tests for the response validator security module.

  file_path: `backend/tests/services/test_response_validator.py`

This module tests the ResponseValidator class to ensure proper detection
of security issues and format validation.

## TestResponseValidator

Test the ResponseValidator class.

### setup_method()

```python
def setup_method(self):
```

Set up test fixtures.

### test_valid_responses()

```python
def test_valid_responses(self):
```

Test that valid responses pass validation.

### test_empty_responses()

```python
def test_empty_responses(self):
```

Test handling of empty responses.

### test_non_string_input()

```python
def test_non_string_input(self, caplog):
```

Test handling of non-string input.

### test_system_instruction_leakage()

```python
def test_system_instruction_leakage(self, caplog):
```

Test detection of system instruction leakage.

### test_verbatim_input_regurgitation()

```python
def test_verbatim_input_regurgitation(self, caplog):
```

Test detection of verbatim input regurgitation for long texts.

### test_no_regurgitation_for_short_input()

```python
def test_no_regurgitation_for_short_input(self):
```

Test that short inputs don't trigger regurgitation check.

### test_ai_refusal_phrases()

```python
def test_ai_refusal_phrases(self, caplog):
```

Test detection of AI refusal phrases.

### test_forbidden_response_patterns()

```python
def test_forbidden_response_patterns(self, caplog):
```

Test detection of forbidden response patterns.

### test_case_insensitive_pattern_matching()

```python
def test_case_insensitive_pattern_matching(self, caplog):
```

Test that pattern matching is case insensitive.

### test_expected_type_validation_summary()

```python
def test_expected_type_validation_summary(self, caplog):
```

Test expected type validation for summary.

### test_expected_type_validation_sentiment()

```python
def test_expected_type_validation_sentiment(self, caplog):
```

Test expected type validation for sentiment.

### test_expected_type_validation_key_points()

```python
def test_expected_type_validation_key_points(self, caplog):
```

Test expected type validation for key points.

### test_expected_type_validation_questions()

```python
def test_expected_type_validation_questions(self, caplog):
```

Test expected type validation for questions.

### test_expected_type_validation_qa()

```python
def test_expected_type_validation_qa(self, caplog):
```

Test expected type validation for Q&A.

### test_no_expected_type_validation()

```python
def test_no_expected_type_validation(self):
```

Test that no validation occurs when expected_type is empty.

### test_whitespace_stripping()

```python
def test_whitespace_stripping(self):
```

Test that responses are properly stripped of whitespace.

### test_combined_validation_failures()

```python
def test_combined_validation_failures(self):
```

Test responses that would trigger multiple validation failures.

### test_forbidden_patterns_compilation()

```python
def test_forbidden_patterns_compilation(self):
```

Test that forbidden patterns are properly compiled.

### test_logging_behavior()

```python
def test_logging_behavior(self, caplog):
```

Test that appropriate logging occurs for various scenarios.

### test_validator_initialization()

```python
def test_validator_initialization(self):
```

Test that ResponseValidator initializes correctly.
