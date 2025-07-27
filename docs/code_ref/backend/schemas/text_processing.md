# Text Processing Schema Definitions

This module defines the complete data contract for text processing functionality,
including request/response models, operation enumerations, and specialized result
structures. It serves as the foundation for AI-powered text analysis operations
such as summarization, sentiment analysis, key point extraction, question generation,
and question-answering capabilities.

## Available Models

Currently re-exported from shared models for compatibility between FastAPI and Streamlit:

### Operations & Status
- `TextProcessingOperation`: Available AI processing operations enum
- `BatchTextProcessingStatus`: Status tracking for batch operations

### Request Models
- `TextProcessingRequest`: Single text processing job with validation
- `BatchTextProcessingRequest`: Multiple text processing jobs with batch limits

### Response Models
- `TextProcessingResponse`: Single operation results with metadata
- `BatchTextProcessingResponse`: Batch operation results with aggregated status
- `BatchTextProcessingItem`: Individual item status within batch responses

### Specialized Results
- `SentimentResult`: Structured sentiment analysis with confidence scoring

## Processing Operations

### Available Operations
- **summarize**: Generate concise summaries of input text
- **sentiment**: Analyze emotional tone and polarity
- **key_points**: Extract main ideas and important concepts
- **questions**: Generate questions about the text content
- **qa**: Answer specific questions about the text

## Usage Examples

Single text processing request:

```python
from app.schemas.text_processing import TextProcessingRequest, TextProcessingOperation

request = TextProcessingRequest(
text="Your text content here...",
operation=TextProcessingOperation.SUMMARIZE,
options={"max_length": 150}
)
```

Question-answering request:

```python
qa_request = TextProcessingRequest(
text="Document content to analyze...",
operation=TextProcessingOperation.QA,
question="What are the main conclusions?"
)
```

Batch processing request:

```python
from app.schemas.text_processing import BatchTextProcessingRequest

batch_request = BatchTextProcessingRequest(
requests=[
TextProcessingRequest(text="Text 1", operation="summarize"),
TextProcessingRequest(text="Text 2", operation="sentiment")
],
batch_id="analysis_batch_001"
)
```

Note: These schemas are currently re-exported from shared models to provide
a single source of truth for both FastAPI and Streamlit applications.
