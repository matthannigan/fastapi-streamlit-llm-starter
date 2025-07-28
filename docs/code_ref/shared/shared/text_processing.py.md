# Pydantic models and enumerations for AI-powered text processing operations.

  file_path: `shared/shared/text_processing.py`

This module defines the complete data contract for text processing functionality,
including request/response models, operation enumerations, and specialized result
structures. It serves as the foundation for AI-powered text analysis operations
such as summarization, sentiment analysis, key point extraction, question generation,
and question-answering capabilities.

The module is designed to support both individual text processing requests and
high-throughput batch operations, with comprehensive validation, error handling,
and metadata tracking throughout the processing pipeline.

## Architecture

The text processing models follow a layered architecture:

1. **Operation Definitions**: Enumerated types that define available processing
operations and their identifiers.

2. **Request Models**: Input validation and structure for both single and batch
text processing requests, with operation-specific parameter validation.

3. **Response Models**: Structured output formats with operation-specific result
fields, metadata, and processing information.

4. **Specialized Results**: Domain-specific result structures for complex
operations like sentiment analysis with confidence scores and explanations.

## Model Categories

### Operation Enumerations

- TextProcessingOperation: Available AI processing operations (summarize,
sentiment, key_points, questions, qa)
- BatchTextProcessingStatus: Status tracking for batch operations

### Request Models

- TextProcessingRequest: Single text processing job with validation rules
- BatchTextProcessingRequest: Multiple text processing jobs with batch limits

### Response Models

- TextProcessingResponse: Single operation results with metadata
- BatchTextProcessingResponse: Batch operation results with aggregated status
- BatchTextProcessingItem: Individual item status within batch responses

### Specialized Results

- SentimentResult: Structured sentiment analysis with confidence scoring

## Processing Operations

Available AI operations and their characteristics:

- **summarize**: Generate concise summaries of input text
- Options: max_length (integer, default varies by model)
- Output: Condensed text preserving key information

- **sentiment**: Analyze emotional tone and polarity
- Options: None required
- Output: SentimentResult with sentiment, confidence, and explanation

- **key_points**: Extract main ideas and important concepts
- Options: max_points (integer, default 5)
- Output: List of key points as strings

- **questions**: Generate questions about the text content
- Options: num_questions (integer, default 3)
- Output: List of relevant questions as strings

- **qa**: Answer specific questions about the text
- Options: None (question provided in request.question field)
- Output: Answer text based on content analysis
- Special: Requires question field in request

## Design Principles

- **Comprehensive Validation**: All input fields include appropriate validators
for length, format, and business rule compliance.
- **Operation-Specific Logic**: Different operations have tailored validation
and response structures optimized for their specific use cases.
- **Batch Processing Support**: Efficient handling of multiple requests with
individual status tracking and error isolation.
- **Metadata Rich**: Extensive metadata capture including processing times,
cache status, and operation context for monitoring and debugging.
- **Flexible Options**: Generic options dictionary allows operation-specific
parameters without breaking schema compatibility.

## Usage Examples

Single text processing request:
```python
from shared.text_processing import TextProcessingRequest, TextProcessingOperation

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
from shared.text_processing import BatchTextProcessingRequest

batch_request = BatchTextProcessingRequest(
requests=[
TextProcessingRequest(text="Text 1", operation="summarize"),
TextProcessingRequest(text="Text 2", operation="sentiment")
],
batch_id="analysis_batch_001"
)
```

Processing response handling:
```python
from shared.text_processing import TextProcessingResponse

# Handle different response types
if response.operation == TextProcessingOperation.SENTIMENT:
sentiment_data = response.sentiment
print(f"Sentiment: {sentiment_data.sentiment} ({sentiment_data.confidence:.2f})")
elif response.operation == TextProcessingOperation.KEY_POINTS:
for point in response.key_points:
print(f"- {point}")
```

## Validation Features

The models include comprehensive validation logic:

- **Text Content**: Minimum/maximum length validation, whitespace trimming,
and empty content detection.
- **Operation Dependencies**: Cross-field validation ensuring required fields
are present for specific operations (e.g., question for Q&A).
- **Batch Limits**: Configurable limits on batch size to prevent resource
exhaustion and ensure reasonable processing times.
- **Parameter Validation**: Type checking and range validation for operation-
specific options and configuration parameters.

## Integration Notes

- **FastAPI Compatibility**: All models are designed for seamless integration
with FastAPI's automatic validation and OpenAPI documentation generation.
- **Serialization Support**: Custom serializers for complex types like datetime
ensure consistent JSON representation across different environments.
- **Cache Integration**: Built-in cache metadata fields support response
caching strategies and cache hit/miss tracking.
- **Error Handling**: Validation errors provide detailed field-level feedback
suitable for client-side error display and API debugging.
- **Monitoring Ready**: Extensive metadata fields support comprehensive
application monitoring, performance tracking, and usage analytics.

## Performance Considerations

- **Efficient Validation**: Validators are optimized for performance with
minimal computational overhead during request processing.
- **Batch Optimization**: Batch processing models support efficient bulk
operations while maintaining individual request traceability.
- **Memory Management**: Response models use optional fields and lazy loading
patterns to minimize memory usage for large batch operations.

## Version History

1.0.0: Initial text processing models with basic operations
1.1.0: Added batch processing support and comprehensive validation
1.2.0: Enhanced sentiment analysis with confidence scoring
1.3.0: Added question generation and Q&A capabilities
1.4.0: Improved metadata tracking and cache integration

## See Also

- app.services.text_processor: Service layer that uses these models
- app.api.v1.text_processing: API endpoints that consume these schemas
- app.schemas: Backend schema registry that imports these models

## Author

FastAPI LLM Starter Team

## License

MIT License
