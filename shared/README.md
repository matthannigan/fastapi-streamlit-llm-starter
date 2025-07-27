# Shared Module

**Common data models and utilities for the FastAPI + Streamlit LLM Starter Template**

This package provides shared Pydantic models, sample data, and utilities used across both the FastAPI backend and Streamlit frontend components of the starter template. It ensures type safety, data consistency, and standardized examples throughout the application.

## 🏗️ Architecture Role

The shared module serves as the **data contract layer** between frontend and backend components:

- **Type Safety**: Shared Pydantic models ensure consistent data structures across services
- **Version Control**: Centralized model definitions prevent version drift between components  
- **Documentation**: Auto-generated schemas provide consistent API documentation
- **Testing**: Standardized sample data ensures consistent examples across all tests and demos

## 📦 Module Structure

```
shared/
├── __init__.py          # Package exports and convenience imports
├── models.py            # Main model exports (facade pattern)
├── sample_data.py       # Standardized sample content and examples
└── text_processing.py   # Core Pydantic models for AI operations
```

## 🔧 Installation

Install the shared module in editable mode from your backend or frontend environment:

```bash
# From project root
source .venv/bin/activate
pip install -e shared/

# Or using the Makefile (handles venv automatically)
make install
```

The shared module is automatically installed when you run `make install` from the project root.

## 📊 Available Models

### Core Processing Models

- **`TextProcessingOperation`**: Enumeration of AI operations (`summarize`, `sentiment`, `key_points`, `questions`, `qa`)
- **`TextProcessingRequest`**: Input validation for single text processing with operation-specific options
- **`TextProcessingResponse`**: Comprehensive response structure with operation-specific result fields
- **`SentimentResult`**: Structured sentiment analysis with confidence scores and explanations

### Batch Processing Models

- **`BatchTextProcessingRequest`**: Multiple text processing requests with batch limits (max 200 items)
- **`BatchTextProcessingResponse`**: Aggregated batch results with individual item status tracking
- **`BatchTextProcessingItem`**: Individual request status within batch operations
- **`BatchTextProcessingStatus`**: Status enumeration (`pending`, `processing`, `completed`, `failed`)

## 🎯 Usage Examples

### Basic Text Processing

```python
from shared.models import TextProcessingRequest, TextProcessingOperation
from shared.sample_data import get_sample_text

# Create a summarization request
request = TextProcessingRequest(
    text=get_sample_text("ai_technology"),
    operation=TextProcessingOperation.SUMMARIZE,
    options={"max_length": 150}
)

# Create a sentiment analysis request
sentiment_request = TextProcessingRequest(
    text=get_sample_text("positive_review"),
    operation=TextProcessingOperation.SENTIMENT
)

# Create a Q&A request (requires question parameter)
qa_request = TextProcessingRequest(
    text=get_sample_text("technical_documentation"),
    operation=TextProcessingOperation.QA,
    question="What authentication method does the API use?"
)
```

### Batch Processing

```python
from shared.models import BatchTextProcessingRequest, TextProcessingRequest

# Create a batch processing request
batch_request = BatchTextProcessingRequest(
    requests=[
        TextProcessingRequest(text="Text 1", operation="summarize"),
        TextProcessingRequest(text="Text 2", operation="sentiment"),
        TextProcessingRequest(text="Text 3", operation="key_points")
    ],
    batch_id="analysis_batch_001"
)
```

### Sample Data Access

```python
from shared.sample_data import (
    get_sample_text, get_sample_request, get_sample_response,
    get_example_options, get_recommended_examples
)

# Get specific sample texts
ai_text = get_sample_text("ai_technology")
business_text = get_sample_text("business_report")

# Get pre-configured request examples
summarize_example = get_sample_request("summarize")
sentiment_example = get_sample_request("sentiment_positive")

# Get UI-friendly example options
example_options = get_example_options()
# Returns: {"ai_technology": "🤖 AI Technology - About AI trends", ...}

# Get operation-specific recommendations
recommended = get_recommended_examples("summarize")
# Returns: ["ai_technology", "climate_change", "business_report"]

# Get complete API examples for documentation
api_example = get_api_example("basic_request")
error_example = get_error_example("validation_error")
```

### Response Handling

```python
from shared.models import TextProcessingResponse, TextProcessingOperation

def handle_response(response: TextProcessingResponse):
    """Example response handler for different operation types."""
    
    if response.operation == TextProcessingOperation.SENTIMENT:
        # Handle sentiment analysis results
        sentiment_data = response.sentiment
        print(f"Sentiment: {sentiment_data.sentiment}")
        print(f"Confidence: {sentiment_data.confidence:.2f}")
        print(f"Explanation: {sentiment_data.explanation}")
        
    elif response.operation == TextProcessingOperation.KEY_POINTS:
        # Handle key points extraction
        print("Key Points:")
        for i, point in enumerate(response.key_points, 1):
            print(f"{i}. {point}")
            
    elif response.operation == TextProcessingOperation.SUMMARIZE:
        # Handle summarization results
        print(f"Summary: {response.result}")
        print(f"Original length: {response.metadata.get('original_length', 'unknown')}")
        
    # Check processing metadata
    if response.cache_hit:
        print("✓ Result served from cache")
    print(f"Processing time: {response.processing_time:.2f}s")
```

## 📝 Sample Data Categories

The `sample_data` module provides comprehensive examples for testing and demonstration:

### Text Content Library
- **`ai_technology`**: AI trends and applications
- **`climate_change`**: Environmental challenges and solutions  
- **`business_report`**: Quarterly earnings and performance metrics
- **`positive_review`**: Customer satisfaction example
- **`negative_review`**: Customer complaint example
- **`technical_documentation`**: API documentation sample
- **`educational_content`**: Science learning material

### UI Integration Support
- **Example Options**: User-friendly descriptions with emojis for UI display
- **Operation Recommendations**: Suggested examples for specific operations
- **Convenience Functions**: Quick access to texts by length (`get_short_text()`, `get_medium_text()`, `get_long_text()`)

### API Documentation Examples
- **Request Examples**: Complete HTTP request examples for each operation
- **Response Examples**: Realistic API responses with proper metadata
- **Error Examples**: Common error scenarios for comprehensive documentation

## 🔍 Model Features

### Comprehensive Validation
- **Text Length**: 10-10,000 character limits with whitespace trimming
- **Operation Dependencies**: Cross-field validation (e.g., question required for Q&A)
- **Type Safety**: Strict type checking with Pydantic v2
- **Parameter Validation**: Range checks for operation-specific options

### Metadata & Monitoring
- **Processing Times**: Execution duration tracking
- **Cache Integration**: Cache hit/miss status tracking
- **Timestamps**: ISO-formatted timestamps for all responses
- **User Context**: Optional user metadata for request tracking

### FastAPI Integration
- **Auto-Documentation**: OpenAPI schema generation with examples
- **Validation Errors**: Detailed field-level error messages
- **Serialization**: Consistent JSON representation across environments

## 📚 Integration Examples

### Backend Service Integration
```python
# In your FastAPI service
from shared.models import TextProcessingRequest, TextProcessingResponse

async def process_text(request: TextProcessingRequest) -> TextProcessingResponse:
    # Service implementation uses shared models
    pass
```

### Frontend Client Integration
```python
# In your Streamlit app or other frontend
from shared.models import TextProcessingRequest, TextProcessingOperation
from shared.sample_data import get_example_options, get_sample_text

# Populate UI with standardized examples
example_options = get_example_options()
selected_example = st.selectbox("Choose example:", example_options.keys())
example_text = get_sample_text(selected_example)
```

### Testing Integration
```python
# In your test files
from shared.sample_data import get_sample_request, get_sample_response

def test_text_processing():
    # Use standardized test data
    request = get_sample_request("summarize")
    expected_response = get_sample_response("summarize")
    # Test implementation...
```

## 🔧 Configuration

### Package Information
- **Distribution Name**: `my_project_shared_lib` (for pip)
- **Version**: `0.1.0`
- **Python Requirements**: `>=3.8`
- **Dependencies**: `pydantic>=2.0`

### Development Setup
```bash
# Install with development dependencies
pip install -e "shared/[dev]"

# Run tests (if test suite is added)
pytest shared/tests/
```

## 🎯 Template Customization

When customizing this starter template for your project:

### ✅ Keep & Extend
- **Core model structure**: The Pydantic model patterns are production-ready
- **Validation patterns**: Comprehensive validation logic provides robustness
- **Sample data framework**: The sample data system supports UI and testing needs

### 🔄 Customize for Your Domain
- **Operation Types**: Replace `TextProcessingOperation` with your business operations
- **Request/Response Models**: Modify fields to match your specific data requirements
- **Sample Content**: Update `STANDARD_SAMPLE_TEXTS` with your domain-specific examples
- **Validation Rules**: Adjust field validators for your business rules

### 📋 Customization Checklist
- [ ] Update operation enumeration with your business operations
- [ ] Modify request/response models for your data structures
- [ ] Replace sample texts with your domain examples
- [ ] Update package name in `pyproject.toml`
- [ ] Adjust validation rules for your requirements
- [ ] Update this README with your project-specific information

## 📖 Additional Resources

- **Backend Integration**: See `backend/app/schemas/` for backend-specific model extensions
- **Frontend Examples**: Check `frontend/app.py` for Streamlit integration patterns  
- **API Documentation**: Auto-generated docs at `/docs` when running the FastAPI server
- **Testing Examples**: View backend tests for comprehensive usage patterns 