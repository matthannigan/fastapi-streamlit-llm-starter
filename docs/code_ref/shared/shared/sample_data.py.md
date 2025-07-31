---
sidebar_label: sample_data
---

# Standardized sample data and example content for AI text processing operations.

  file_path: `shared/shared/sample_data.py`

This module provides a comprehensive collection of sample texts, example requests,
response templates, and API examples for consistent use across testing, documentation,
and user interfaces. It ensures standardized examples throughout the application
while supporting different text types and processing operations.

# Sample Data Categories

## Text Content Library
Curated sample texts covering various domains:
- **AI Technology**: Content about artificial intelligence trends and applications
- **Climate Change**: Environmental topics for educational and analytical examples
- **Business Reports**: Professional content for summarization and analysis
- **Product Reviews**: Positive and negative sentiment examples
- **Technical Documentation**: API and technical content for Q&A operations
- **Educational Content**: Learning materials for question generation

## Example Templates
Pre-configured request and response examples:
- **Request Examples**: Complete TextProcessingRequest objects for each operation
- **Response Examples**: Realistic TextProcessingResponse objects with metadata
- **API Examples**: HTTP request/response examples for documentation
- **Error Examples**: Common error scenarios for testing and documentation

## UI Integration Support
User interface components and recommendations:
- **Example Options**: User-friendly descriptions for UI display
- **Operation Recommendations**: Suggested examples for specific operations
- **Convenience Functions**: Quick access to texts by length and domain

# Key Features

## Consistency Guarantees
- **Standardized Content**: All examples use the same base texts across components
- **Validated Responses**: Response examples match actual API response structure
- **UI Consistency**: Example descriptions and recommendations are centralized

## Testing Support
- **Comprehensive Coverage**: Examples for all supported operations and scenarios
- **Error Cases**: Predefined error examples for negative testing
- **Performance Testing**: Texts of varying lengths for performance validation

## Documentation Integration
- **API Documentation**: Ready-to-use examples for OpenAPI documentation
- **User Guides**: Consistent examples for tutorials and help content
- **Developer Examples**: Code snippets with realistic data

## Usage Examples

Basic text retrieval:
```python
from shared.sample_data import get_sample_text, get_medium_text

# Get specific sample text
ai_text = get_sample_text("ai_technology")

# Get text by length category
demo_text = get_medium_text()
```

### UI integration

```python
from shared.sample_data import get_example_options, get_recommended_examples

# Get options for dropdown/buttons
options = get_example_options()

# Get operation-specific recommendations
recommendations = get_recommended_examples("summarize")
```

### API documentation

```python
from shared.sample_data import get_api_example, get_error_example

# Get complete API request example
request_example = get_api_example("basic_request")

# Get error response example
error_example = get_error_example("validation_error")
```

## Data Validation

All sample data includes validation to ensure:
- Text length compliance with application limits
- Proper formatting and encoding
- Realistic content that demonstrates features effectively
- Error examples that match actual API error formats

## Integration Notes

- **Frontend Integration**: Example options and recommendations support dynamic UI
- **Backend Testing**: Request/response examples validate service functionality
- **Documentation**: API examples generate comprehensive API documentation
- **Performance Testing**: Varied text lengths support load and performance testing

This module serves as the single source of truth for all example content,
ensuring consistency across documentation, testing, and user experiences.
