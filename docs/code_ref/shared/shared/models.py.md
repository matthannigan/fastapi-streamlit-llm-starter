---
sidebar_label: models
---

# Shared Pydantic models module - exports for application-wide use.

  file_path: `shared/shared/models.py`

This module serves as the primary export interface for all Pydantic models used
throughout the AI text processing application. It re-exports models from the
text_processing module to provide a clean, centralized import interface.

## Exported Models

TextProcessingOperation: Enumeration of available AI processing operations
TextProcessingRequest: Input validation model for single text processing
BatchTextProcessingRequest: Input validation model for batch processing
SentimentResult: Structured sentiment analysis results with confidence scoring
TextProcessingResponse: Comprehensive response model with operation-specific fields
BatchTextProcessingStatus: Status enumeration for batch operation tracking
BatchTextProcessingItem: Individual item status within batch processing
BatchTextProcessingResponse: Aggregated batch processing results

## Usage

```python
from shared.models import TextProcessingRequest, TextProcessingOperation

# Create a processing request
request = TextProcessingRequest(
text="Sample text content",
operation=TextProcessingOperation.SUMMARIZE,
options={"max_length": 150}
)
```

## Note

This module acts as a facade over the text_processing module, providing
stable import paths for client code while allowing internal reorganization.
