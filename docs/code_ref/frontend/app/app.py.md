---
sidebar_label: app
---

# AI Text Processing Frontend Application - Streamlit Starter Template.

  file_path: `frontend/app/app.py`

This module serves as a comprehensive Streamlit frontend application demonstrating best practices
for building production-ready AI applications. It provides a complete web interface for an AI
text processing service and serves as a starter template for developers building similar applications.

# Starter Template Features

This application exemplifies modern Streamlit development patterns and can be used as a foundation
for building AI-powered web applications with the following characteristics:

## Core Application Capabilities
- **Text summarization** with configurable length parameters
- **Sentiment analysis** with confidence scoring and explanations
- **Key point extraction** with customizable count settings
- **Question generation** for educational and content creation purposes
- **Question & Answer** functionality for interactive text exploration

## Production-Ready Features
- **Real-time API health monitoring** with status indicators
- **Dynamic operation configuration** based on backend capabilities
- **Intelligent example text system** with operation-specific recommendations
- **Multi-modal input support** (text entry, file upload) with validation
- **Results persistence** with download functionality and session management
- **Responsive design** with progress indicators and user feedback
- **Comprehensive error handling** with graceful degradation

## Architecture Patterns Demonstrated

### Frontend Architecture
- **Modular component design** with single-responsibility functions
- **Separation of concerns** between UI, logic, and data layers
- **Configuration-driven behavior** with environment-specific settings
- **Shared data models** for type safety and API consistency

### User Experience Patterns
- **Progressive disclosure** with collapsible sections and smart defaults
- **Contextual assistance** through operation-specific recommendations
- **Immediate feedback** with real-time validation and status updates
- **Accessibility considerations** with semantic markup and help text

### Integration Patterns
- **Async API communication** with proper error handling and timeouts
- **Dynamic UI generation** based on backend capabilities
- **Session state management** for stateful user interactions
- **File handling** with validation, preview, and encoding support

## Template Customization Guide

### For AI Applications
1. **Replace AI operations**: Modify the text processing operations to match your AI service
2. **Update models**: Replace shared models with your domain-specific data structures
3. **Customize UI**: Adapt the interface components to your application's needs
4. **Configure examples**: Update sample data to reflect your use cases

### For General Applications
1. **API integration**: Replace the API client with your backend communication layer
2. **Data processing**: Modify input/output handling for your data types
3. **UI components**: Adapt the layout and controls to your application requirements
4. **Configuration**: Update settings and environment variables for your deployment

## Quick Start for Developers

```python
# Basic application structure
def main():
    display_header()                    # Application branding
    check_api_health()                 # Backend connectivity
    operation, options = select_operation_sidebar()  # Dynamic configuration
    examples_sidebar()                 # Contextual examples
    
    # Main interaction flow
    text_content, question = display_text_input()
    if st.button("Process"):
        request = create_processing_request(text_content, operation, options)
        response = run_async(api_client.process_text(request))
        handle_processing_result(response, operation)
    
    # Results display
    display_results(response, operation)
```

## Deployment Examples

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
streamlit run app.py --server.runOnSave=true
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up frontend

# Or standalone container
docker build -t my-ai-app .
docker run -p 8501:8501 my-ai-app
```

### Production Deployment
```bash
# With environment configuration
export API_BASE_URL="https://api.myapp.com"
export STREAMLIT_ENV="production"
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

## Dependencies and Extensions

### Core Dependencies
- **streamlit**: Modern web application framework for Python
- **httpx**: Async HTTP client for API communication
- **pydantic**: Data validation and settings management

### Custom Modules
- **shared.models**: Type-safe data models shared with backend
- **shared.sample_data**: Curated example content for demonstrations
- **utils.api_client**: Robust API communication with error handling
- **config**: Environment-aware configuration management

## Template Benefits

This starter template provides:
- **Rapid prototyping** for AI application concepts
- **Production-ready patterns** for deployment and scaling
- **Best practices** for Streamlit development and API integration
- **Extensible architecture** for custom requirements
- **Comprehensive documentation** for developer onboarding

Use this as a foundation for building sophisticated AI applications while maintaining
code quality, user experience, and deployment readiness.

Author: AI Text Processing Team
Version: 1.0.0
Template: FastAPI + Streamlit + AI Starter

## display_header()

```python
def display_header() -> None:
```

Display the main application header with title and description.

Creates a professional header section with the application title,
description, and visual separator. This provides users with immediate
context about the application's purpose and capabilities.

## check_api_health()

```python
def check_api_health() -> bool:
```

Check the health status of the backend API service.

Performs a health check against the backend API and displays the
connection status in the sidebar. This provides immediate feedback
to users about service availability and helps with troubleshooting.

Returns:
    bool: True if the API is healthy and accessible, False otherwise.
    
Side Effects:
    - Displays health status in the sidebar
    - Shows error message if API is unavailable

## get_operation_info()

```python
def get_operation_info() -> Optional[Dict[str, Any]]:
```

Retrieve available operations and their configurations from the API.

Fetches the list of supported text processing operations from the backend
API, including their descriptions and configurable options. This enables
dynamic UI generation based on available backend capabilities.

Returns:
    Optional[Dict[str, Any]]: Dictionary mapping operation IDs to their
    configuration details, or None if the API call fails.
    
Note:
    The returned dictionary structure:
    {
        "operation_id": {
            "name": "Display Name",
            "description": "Operation description",
            "options": ["max_length", "max_points", ...]
        }
    }

## select_operation_sidebar()

```python
def select_operation_sidebar() -> Tuple[Optional[str], Dict[str, Any]]:
```

Create the sidebar interface for operation selection and configuration.

Builds a dynamic sidebar that allows users to:
1. Select from available text processing operations
2. Configure operation-specific parameters (length, points, questions)
3. View operation descriptions and requirements

The function dynamically generates configuration controls based on the
selected operation's supported options, providing a responsive UI that
adapts to backend capabilities.

Returns:
    Tuple[Optional[str], Dict[str, Any]]: A tuple containing:
        - The selected operation ID (None if no operations available)
        - A dictionary of configured options for the selected operation
        
Side Effects:
    - Renders operation selection dropdown in sidebar
    - Renders parameter controls for selected operation
    - Updates session state with selected operation

## make_example_buttons()

```python
def make_example_buttons(example_options: Dict[str, str]) -> None:
```

Create interactive buttons for loading example texts.

Generates a grid of buttons allowing users to quickly load predefined
example texts. This improves user experience by providing immediate
content to test different operations without requiring manual input.

Args:
    example_options: Dictionary mapping text type IDs to their display names.
    
Side Effects:
    - Creates button grid in the current Streamlit context
    - Updates session state when example is selected
    - Triggers page rerun when example is loaded
    - Displays success/error messages

## examples_sidebar()

```python
def examples_sidebar() -> None:
```

Create the sidebar section for example text selection.

Builds an intelligent example selection interface that:
1. Shows operation-specific recommendations first
2. Provides access to all available examples
3. Displays preview of currently loaded text
4. Identifies which example is currently active

The function leverages the shared sample data module to provide
consistent examples across the application and offers contextual
recommendations based on the selected operation.

Side Effects:
    - Renders example selection interface in sidebar
    - Updates session state with selected example text
    - Displays text preview and identification

## display_text_input()

```python
def display_text_input() -> Tuple[str, Optional[str]]:
```

Display and handle text input interface with multiple input methods.

Creates a comprehensive text input section that supports:
1. Direct text entry via textarea
2. File upload for text documents (.txt, .md)
3. Character count validation
4. File preview functionality
5. Question input for Q&A operations

The function adapts its interface based on the selected operation,
showing additional fields when required (e.g., question field for Q&A).

Returns:
    Tuple[str, Optional[str]]: A tuple containing:
        - The input text content (empty string if none provided)
        - The question text for Q&A operations (None for other operations)
        
Side Effects:
    - Renders text input interface
    - Displays file upload controls when selected
    - Shows character count and validation messages
    - Handles file reading and error reporting

## normalize_whitespace()

```python
def normalize_whitespace(text: str) -> str:
```

Normalize whitespace in text while preserving paragraph structure.

This function cleans up text formatting by:
1. Removing leading/trailing whitespace from each line
2. Replacing multiple spaces/tabs with single spaces
3. Standardizing paragraph breaks (max 2 consecutive newlines)
4. Preserving overall text structure and readability

This is particularly useful for example texts that may have formatting
inconsistencies from various sources while maintaining readability.

Args:
    text: The input text string to normalize.
    
Returns:
    str: The normalized text with standardized whitespace formatting.
    
Example:
    >>> normalize_whitespace("Line 1   with   spaces\n\n\n\nLine 2")
    "Line 1 with spaces\n\nLine 2"

## display_results()

```python
def display_results(response: Any, operation: str) -> None:
```

Display comprehensive processing results with operation-specific formatting.

Creates a rich results display that adapts to different operation types:
- Summary operations: Shows formatted summary text
- Sentiment analysis: Displays sentiment with confidence visualization
- Key points: Lists points in numbered format
- Questions: Shows generated questions in organized list
- Q&A: Displays answer with proper formatting

The function also provides metadata including processing time, word count,
and debug information when enabled.

Args:
    response: The API response object containing processing results.
    operation: The operation type that was performed.
    
Side Effects:
    - Renders formatted results section
    - Displays operation metrics and metadata
    - Shows debug information if configured
    - Creates downloadable results

## create_processing_request()

```python
def create_processing_request(text_content: str, selected_operation: str, question: Optional[str], options: Dict[str, Any]) -> TextProcessingRequest:
```

Create a validated text processing request object.

Constructs a properly formatted TextProcessingRequest using the shared
models from the backend. This ensures type safety and validation before
sending requests to the API.

Args:
    text_content: The text to be processed.
    selected_operation: The operation type identifier.
    question: Optional question for Q&A operations.
    options: Dictionary of operation-specific configuration options.
    
Returns:
    TextProcessingRequest: A validated request object ready for API submission.
    
Raises:
    ValidationError: If the request parameters are invalid.

## handle_processing_result()

```python
def handle_processing_result(response: Any, selected_operation: str) -> None:
```

Handle and store successful processing results.

Processes the API response and updates the session state to enable
result display and download functionality. This function centralizes
result handling logic and provides consistent success feedback.

Args:
    response: The successful API response object.
    selected_operation: The operation that was performed.
    
Side Effects:
    - Updates session state with response data
    - Displays success message
    - Enables result display and download

## display_usage_tips()

```python
def display_usage_tips() -> None:
```

Display helpful usage tips and best practices.

Creates an informative sidebar section with practical advice for
getting the best results from the text processing operations.
This improves user experience by setting proper expectations
and providing guidance.

Side Effects:
    - Renders tips section in the current column context

## handle_results_download()

```python
def handle_results_download() -> None:
```

Handle results download functionality.

Provides users with the ability to download their processing results
as a formatted JSON file. This enables result preservation and
integration with other tools or workflows.

Side Effects:
    - Creates download button if results are available
    - Generates JSON file with formatted results
    - Provides appropriate filename with operation type

## main()

```python
def main() -> None:
```

Main application entry point and orchestration function.

Coordinates the entire application flow:
1. Displays header and checks API health
2. Sets up sidebar with operation selection and examples
3. Creates main content area with input and processing
4. Handles result display and download functionality
5. Manages error states and user feedback

This function demonstrates proper Streamlit application structure
with clear separation of concerns and comprehensive error handling.

Side Effects:
    - Renders complete application interface
    - Manages session state
    - Handles API communication
    - Provides user feedback and error handling
