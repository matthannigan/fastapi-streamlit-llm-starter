---
sidebar_label: test_text_processing_schemas
---

# Tests for text processing schemas.

  file_path: `backend/tests/shared_schemas/test_text_processing_schemas.py`
Combined from test_models.py and test_validation_schemas.py

## TestTextProcessingRequest

Test TextProcessingRequest model.

### test_valid_request()

```python
def test_valid_request(self):
```

Test valid request creation.

### test_qa_request_with_question()

```python
def test_qa_request_with_question(self):
```

Test Q&A request with question.

### test_text_too_short()

```python
def test_text_too_short(self):
```

Test validation fails for text too short.

### test_text_too_long()

```python
def test_text_too_long(self):
```

Test validation fails for text too long.

### test_invalid_operation()

```python
def test_invalid_operation(self):
```

Test validation fails for invalid operation.

## TestTextProcessingResponse

Test TextProcessingResponse model.

### test_basic_response()

```python
def test_basic_response(self):
```

Test basic response creation.

### test_sentiment_response()

```python
def test_sentiment_response(self):
```

Test sentiment analysis response.

### test_key_points_response()

```python
def test_key_points_response(self):
```

Test key points response.

### test_questions_response()

```python
def test_questions_response(self):
```

Test questions response.

## TestSentimentResult

Test SentimentResult model.

### test_valid_sentiment()

```python
def test_valid_sentiment(self):
```

Test valid sentiment result.

### test_confidence_bounds()

```python
def test_confidence_bounds(self):
```

Test confidence score bounds validation.

## TestTextProcessingOperation

Test TextProcessingOperation enum.

### test_all_operations()

```python
def test_all_operations(self):
```

Test all operation values are valid.
