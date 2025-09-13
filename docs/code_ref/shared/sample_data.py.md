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

Usage Examples:
    Basic text retrieval:
        ```python
        from shared.sample_data import get_sample_text, get_medium_text
        
        # Get specific sample text
        ai_text = get_sample_text("ai_technology")
        
        # Get text by length category
        demo_text = get_medium_text()
        ```
    
    UI integration:
        ```python
        from shared.sample_data import get_example_options, get_recommended_examples
        
        # Get options for dropdown/buttons
        options = get_example_options()
        
        # Get operation-specific recommendations
        recommendations = get_recommended_examples("summarize")
        ```
    
    API documentation:
        ```python
        from shared.sample_data import get_api_example, get_error_example
        
        # Get complete API request example
        request_example = get_api_example("basic_request")
        
        # Get error response example
        error_example = get_error_example("validation_error")
        ```

Data Validation:
    All sample data includes validation to ensure:
    - Text length compliance with application limits
    - Proper formatting and encoding
    - Realistic content that demonstrates features effectively
    - Error examples that match actual API error formats

Integration Notes:
    - **Frontend Integration**: Example options and recommendations support dynamic UI
    - **Backend Testing**: Request/response examples validate service functionality
    - **Documentation**: API examples generate comprehensive API documentation
    - **Performance Testing**: Varied text lengths support load and performance testing

This module serves as the single source of truth for all example content,
ensuring consistency across documentation, testing, and user experiences.

## get_sample_text()

```python
def get_sample_text(text_type: str) -> str:
```

Get a standard sample text by type.

Args:
    text_type: Type of sample text to retrieve
    
Returns:
    The requested sample text
    
Raises:
    KeyError: If the text type is not found

## get_sample_request()

```python
def get_sample_request(operation: str) -> TextProcessingRequest:
```

Get a standard request example for an operation.

Args:
    operation: The operation type to get an example for
    
Returns:
    A standard TextProcessingRequest example
    
Raises:
    KeyError: If the operation is not found

## get_sample_response()

```python
def get_sample_response(operation: str) -> TextProcessingResponse:
```

Get a standard response example for an operation.

Args:
    operation: The operation type to get an example for
    
Returns:
    A standard TextProcessingResponse example
    
Raises:
    KeyError: If the operation is not found

## get_all_sample_texts()

```python
def get_all_sample_texts() -> Dict[str, str]:
```

Get all available sample texts.

## get_all_request_examples()

```python
def get_all_request_examples() -> Dict[str, TextProcessingRequest]:
```

Get all available request examples.

## get_all_response_examples()

```python
def get_all_response_examples() -> Dict[str, TextProcessingResponse]:
```

Get all available response examples.

## get_api_example()

```python
def get_api_example(example_type: str) -> Dict[str, Any]:
```

Get a standard API call example.

Args:
    example_type: Type of API example to retrieve
    
Returns:
    Dictionary containing the API call example
    
Raises:
    KeyError: If the example type is not found

## get_error_example()

```python
def get_error_example(error_type: str) -> Dict[str, Any]:
```

Get a standard error response example.

Args:
    error_type: Type of error example to retrieve
    
Returns:
    Dictionary containing the error example
    
Raises:
    KeyError: If the error type is not found

## get_short_text()

```python
def get_short_text() -> str:
```

Get a short sample text suitable for quick examples.

## get_medium_text()

```python
def get_medium_text() -> str:
```

Get a medium-length sample text suitable for most examples.

## get_long_text()

```python
def get_long_text() -> str:
```

Get a longer sample text suitable for comprehensive examples.

## get_technical_text()

```python
def get_technical_text() -> str:
```

Get a technical sample text suitable for documentation examples.

## get_business_text()

```python
def get_business_text() -> str:
```

Get a business-oriented sample text.

## get_example_options()

```python
def get_example_options() -> Dict[str, str]:
```

Get all available example options with their user-friendly descriptions.

Returns:
    Dictionary mapping text type keys to display descriptions

## get_example_description()

```python
def get_example_description(text_type: str) -> str:
```

Get the user-friendly description for a specific text type.

Args:
    text_type: Type of sample text to get description for
    
Returns:
    The user-friendly description string
    
Raises:
    KeyError: If the text type is not found

## get_recommended_examples()

```python
def get_recommended_examples(operation: str) -> List[str]:
```

Get recommended example texts for a specific operation.

Args:
    operation: The operation type to get recommendations for
    
Returns:
    List of recommended text type keys for the operation

## get_all_operation_recommendations()

```python
def get_all_operation_recommendations() -> Dict[str, List[str]]:
```

Get all operation recommendations.
