#!/usr/bin/env python3
"""AI Text Processing Frontend Application - Streamlit Starter Template.

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
"""

import streamlit as st
import json
import re
from typing import Dict, Any, Optional, Tuple

from shared.models import TextProcessingRequest, TextProcessingOperation
from shared.sample_data import (
    get_sample_text,
    get_all_sample_texts,
    get_example_options,
    get_recommended_examples
)
from utils.api_client import api_client, run_async
from config import settings

# Configure Streamlit page with professional defaults
st.set_page_config(
    page_title=settings.page_title,
    page_icon=settings.page_icon,
    layout=settings.layout if settings.layout in ("centered", "wide") else "wide",
    initial_sidebar_state="expanded"
)


def display_header() -> None:
    """Display the main application header with title and description.
    
    Creates a professional header section with the application title,
    description, and visual separator. This provides users with immediate
    context about the application's purpose and capabilities.
    """
    st.title("🤖 AI Text Processor")
    st.markdown(
        "Process text using advanced AI models. Choose from summarization, "
        "sentiment analysis, key point extraction, and more!"
    )
    st.divider()


def check_api_health() -> bool:
    """Check the health status of the backend API service.

    Performs a health check against the backend API and displays the
    connection status in the sidebar. This provides immediate feedback
    to users about service availability and helps with troubleshooting.

    Returns:
        bool: True if the API is healthy and accessible, False otherwise.

    Side Effects:
        - Displays health status in the sidebar
        - Shows error message if API is unavailable
    """
    with st.sidebar:
        st.subheader("🔧 System Status")

        # Perform async health check with error handling
        health_status = run_async(api_client.health_check())

        if health_status:
            st.success("✅ API Connected")

            # Get detailed cache status from internal API for security info
            cache_healthy = health_status.get("cache_healthy")

            if cache_healthy is not None:
                # Fetch detailed cache status from internal API
                cache_status = run_async(api_client.get_cache_status())

                if cache_status:
                    redis_status = cache_status.get("redis", {}).get("status")
                    security_info = cache_status.get("security", {})
                    tls_enabled = security_info.get("configuration", {}).get("tls_enabled", False)

                    if cache_healthy is True and redis_status == "connected":
                        # Redis is connected and healthy
                        if tls_enabled:
                            st.success("✅ TLS-secure Redis active 🔒")
                        else:
                            st.warning("⚠️ Insecure Redis cache active")
                    elif cache_healthy is False:
                        # Redis explicitly failed
                        st.warning("❌ Redis failure")
                    else:
                        # Memory-only fallback
                        st.info("🔄 Memory Cache active")
                else:
                    # Fallback if cache status unavailable
                    if cache_healthy is True:
                        st.info("✅ Cache active")
                    elif cache_healthy is False:
                        st.warning("❌ Cache failure")
                    else:
                        st.info("🔄 Memory Cache active")
        else:
            st.error("❌ API Unavailable")
            st.warning("Please ensure the backend service is running.")
            return False

        return True


def get_operation_info() -> Optional[Dict[str, Any]]:
    """Retrieve available operations and their configurations from the API.
    
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
    """
    operations = run_async(api_client.get_operations())
    if operations:
        return {op['id']: op for op in operations['operations']}
    return None


def select_operation_sidebar() -> Tuple[Optional[str], Dict[str, Any]]:
    """Create the sidebar interface for operation selection and configuration.
    
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
    """
    with st.sidebar:
        st.subheader("⚙️ Configuration")

        # Fetch and validate available operations
        operations_info = get_operation_info()
        if not operations_info:
            st.error("Failed to load operations")
            return None, {}

        # Create user-friendly operation selection dropdown
        operation_options = {
            op_id: f"{info['name']} - {info['description']}"
            for op_id, info in operations_info.items()
        }

        selected_op = st.selectbox(
            "Choose Operation",
            options=list(operation_options.keys()),
            format_func=lambda x: operation_options[x],
            key="operation_select",
            help="Select the type of text processing you want to perform"
        )

        # Validate selection
        if selected_op is None:
            return None, {}

        # Generate operation-specific configuration controls
        options = {}
        op_info = operations_info[selected_op]

        # Summarization length control
        if "max_length" in op_info.get("options", []):
            options["max_length"] = st.slider(
                "Summary Length (words)",
                min_value=50,
                max_value=500,
                value=150,
                step=25,
                help="Maximum number of words in the generated summary"
            )

        # Key points count control
        if "max_points" in op_info.get("options", []):
            options["max_points"] = st.slider(
                "Number of Key Points",
                min_value=3,
                max_value=10,
                value=5,
                help="Maximum number of key points to extract"
            )

        # Questions count control
        if "num_questions" in op_info.get("options", []):
            options["num_questions"] = st.slider(
                "Number of Questions",
                min_value=3,
                max_value=10,
                value=5,
                help="Number of questions to generate about the text"
            )

        return selected_op, options


def make_example_buttons(example_options: Dict[str, str]) -> None:
    """Create interactive buttons for loading example texts.
    
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
    """
    cols = st.columns(2)
    for i, (text_type, description) in enumerate(example_options.items()):
        col = cols[i % 2]
        with col:
            if st.button(
                description, 
                key=f"example_{text_type}", 
                use_container_width=True,
                help=f"Load {text_type.replace('_', ' ').title()} example text"
            ):
                try:
                    example_text = get_sample_text(text_type)
                    # Normalize whitespace for consistent formatting
                    st.session_state['text_input'] = normalize_whitespace(example_text)
                    st.success(f"Loaded {text_type.replace('_', ' ').title()} example!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading example: {e}")


def examples_sidebar() -> None:
    """Create the sidebar section for example text selection.
    
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
    """
    with st.sidebar:
        st.subheader("📚 Example Texts")
        
        # Load standardized example options
        example_options = get_example_options()

        # Provide operation-specific recommendations
        current_operation = st.session_state.get("operation_select")
        if current_operation:
            recommended = get_recommended_examples(current_operation)
            if recommended:
                st.markdown(f"**Recommended for {current_operation.replace('_', ' ').title()}:**")

                # Display recommended examples with star indicator
                for text_type in recommended:
                    if text_type in example_options:
                        description = example_options[text_type]
                        if st.button(
                            f"⭐ {description}", 
                            key=f"rec_{text_type}", 
                            use_container_width=True,
                            help=f"Recommended example for {current_operation}"
                        ):
                            try:
                                example_text = get_sample_text(text_type)
                                st.session_state['text_input'] = normalize_whitespace(example_text)
                                st.success(f"Loaded {text_type.replace('_', ' ').title()} example!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error loading example: {e}")
            
                # Provide access to all examples in expandable section
                with st.expander("**All Examples:**"):
                    make_example_buttons(example_options)
        else:
            # Show all examples when no operation is selected
            st.markdown("**Choose from standardized examples:**")
            make_example_buttons(example_options)

        # Display preview and identification of current text
        if st.session_state.get('text_input'):
            current_text = st.session_state['text_input']
            # Attempt to identify which example is currently loaded
            for text_type, sample_text in get_all_sample_texts().items():
                if current_text.strip() == sample_text.strip():
                    st.info(f"Currently loaded: {text_type.replace('_', ' ').title()}")
                    st.caption("Preview:")
                    preview_text = current_text[:200] + "..." if len(current_text) > 200 else current_text
                    st.text(preview_text)
                    break


def display_text_input() -> Tuple[str, Optional[str]]:
    """Display and handle text input interface with multiple input methods.
    
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
    """
    st.subheader("📝 Input Text")

    # Input method selection
    input_method = st.radio(
        "Input Method",
        ["Type/Paste Text", "Upload File"],
        horizontal=True,
        help="Choose how you want to provide the text for processing"
    )

    text_content = ""

    if input_method == "Type/Paste Text":
        # Direct text input with validation
        text_content = st.text_area(
            "Enter your text here:",
            height=200,
            max_chars=settings.max_text_length,
            placeholder="Paste or type the text you want to process...",
            value=st.session_state.get('text_input', ''),
            help=f"Maximum {settings.max_text_length} characters allowed"
        )
    else:
        # File upload handling
        uploaded_file = st.file_uploader(
            "Upload a text file",
            type=['txt', 'md'],
            help="Upload a .txt or .md file (UTF-8 encoded)",
            accept_multiple_files=False
        )

        if uploaded_file is not None:
            try:
                # Read and decode file content
                text_content = str(uploaded_file.read(), "utf-8")
                file_size = len(text_content)
                
                # Validate file size
                if file_size > settings.max_text_length:
                    st.error(f"File too large ({file_size} characters). Maximum allowed: {settings.max_text_length}")
                    text_content = ""
                else:
                    st.success(f"File uploaded successfully! ({file_size} characters)")

                    # Show expandable preview
                    with st.expander("Preview uploaded text"):
                        preview_text = text_content[:500] + "..." if len(text_content) > 500 else text_content
                        st.text(preview_text)
                        
            except UnicodeDecodeError:
                st.error("Error: File must be UTF-8 encoded text")
                text_content = ""
            except Exception as e:
                st.error(f"Error reading file: {e}")
                text_content = ""

    # Operation-specific additional inputs
    question = None
    if st.session_state.get("operation_select") == "qa":
        question = st.text_input(
            "Enter your question about the text:",
            placeholder="What is the main topic discussed in this text?",
            help="Be specific and clear for best results"
        )

    return text_content, question


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text while preserving paragraph structure.

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
        >>> normalize_whitespace("Line 1   with   spaces\\n\\n\\n\\nLine 2")
        "Line 1 with spaces\\n\\nLine 2"
    """
    # Remove leading/trailing whitespace from each line
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines]

    # Rejoin lines and handle paragraph breaks
    normalized = '\n'.join(cleaned_lines)

    # Replace multiple spaces/tabs with single space
    normalized = re.sub(r'[ \t]+', ' ', normalized)

    # Clean up multiple newlines while preserving paragraph breaks
    normalized = re.sub(r'\n\s*\n', '\n\n', normalized)

    # Limit to maximum of 2 consecutive newlines (paragraph break)
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)

    # Remove any leading/trailing whitespace from the entire text
    return normalized.strip()


def display_results(response: Any, operation: str) -> None:
    """Display comprehensive processing results with operation-specific formatting.
    
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
    """
    st.subheader("📊 Results")

    # Display processing metadata in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Operation", operation.replace("_", " ").title())
    with col2:
        if response.processing_time:
            st.metric("Processing Time", f"{response.processing_time:.2f}s")
    with col3:
        word_count = response.metadata.get("word_count", "N/A")
        st.metric("Word Count", word_count)

    st.divider()

    # Display results based on operation type
    if operation == "summarize":
        st.markdown("### 📋 Summary")
        st.write(response.result)

    elif operation == "sentiment":
        st.markdown("### 🎭 Sentiment Analysis")
        sentiment = response.sentiment

        # Color-coded sentiment display
        color_map = {
            "positive": "green",
            "negative": "red",
            "neutral": "gray"
        }
        color = color_map.get(sentiment.sentiment, "gray")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Sentiment:** :{color}[{sentiment.sentiment.title()}]")
            st.progress(sentiment.confidence)
            st.caption(f"Confidence: {sentiment.confidence:.2%}")

        with col2:
            st.markdown("**Explanation:**")
            st.write(sentiment.explanation)

    elif operation == "key_points":
        st.markdown("### 🎯 Key Points")
        for i, point in enumerate(response.key_points, 1):
            st.markdown(f"{i}. {point}")

    elif operation == "questions":
        st.markdown("### ❓ Generated Questions")
        for i, question in enumerate(response.questions, 1):
            st.markdown(f"{i}. {question}")

    elif operation == "qa":
        st.markdown("### 💬 Answer")
        st.write(response.result)

    # Optional debug information
    if settings.show_debug_info:
        with st.expander("🔍 Debug Information"):
            st.json(response.model_dump())


def create_processing_request(
    text_content: str, 
    selected_operation: str, 
    question: Optional[str], 
    options: Dict[str, Any]
) -> TextProcessingRequest:
    """Create a validated text processing request object.
    
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
    """
    return TextProcessingRequest(
        text=text_content,
        operation=TextProcessingOperation(selected_operation),
        question=question,
        options=options
    )


def handle_processing_result(response: Any, selected_operation: str) -> None:
    """Handle and store successful processing results.
    
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
    """
    if response and response.success:
        # Store results in session state for display and download
        st.session_state['last_response'] = response
        st.session_state['last_operation'] = selected_operation
        st.success("✅ Processing completed!")
    else:
        st.error("❌ Processing failed. Please try again.")


def display_usage_tips() -> None:
    """Display helpful usage tips and best practices.
    
    Creates an informative sidebar section with practical advice for
    getting the best results from the text processing operations.
    This improves user experience by setting proper expectations
    and providing guidance.
    
    Side Effects:
        - Renders tips section in the current column context
    """
    st.subheader("💡 Tips")
    st.markdown("""
    **For best results:**
    - Use clear, well-structured text
    - Longer texts work better for summarization
    - Be specific with your questions for Q&A
    - Try different operations to explore your text
    - Check the recommended examples for each operation
    
    **Text Requirements:**
    - Minimum 10 characters
    - Maximum 10,000 characters
    - UTF-8 encoding for uploaded files
    """)


def handle_results_download() -> None:
    """Handle results download functionality.
    
    Provides users with the ability to download their processing results
    as a formatted JSON file. This enables result preservation and
    integration with other tools or workflows.
    
    Side Effects:
        - Creates download button if results are available
        - Generates JSON file with formatted results
        - Provides appropriate filename with operation type
    """
    if 'last_response' in st.session_state and 'last_operation' in st.session_state:
        if st.button("📥 Download Results", help="Download results as JSON file"):
            results_json = json.dumps(
                st.session_state['last_response'].model_dump(), 
                indent=2,
                default=str  # Handle datetime serialization
            )
            st.download_button(
                label="Download as JSON",
                data=results_json,
                file_name=f"ai_text_processing_results_{st.session_state['last_operation']}.json",
                mime="application/json"
            )


def main() -> None:
    """Main application entry point and orchestration function.
    
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
    """
    # Initialize application interface
    display_header()

    # Verify backend connectivity
    if not check_api_health():
        st.stop()

    # Setup operation selection and configuration
    selected_operation, options = select_operation_sidebar()
    if not selected_operation:
        st.stop()
    
    # Type assertion for type checker - we know selected_operation is not None here
    assert selected_operation is not None

    # Add example text selection interface
    examples_sidebar()

    # Main content layout
    col1, col2 = st.columns([2, 1])

    with col1:
        # Text input handling
        text_content, question = display_text_input()

        # Processing trigger
        if st.button("🚀 Process Text", type="primary", use_container_width=True):
            # Input validation
            if not text_content.strip():
                st.error("Please enter some text to process.")
                return

            if selected_operation == "qa" and not question:
                st.error("Please enter a question for Q&A operation.")
                return

            # Create and validate request
            try:
                request = create_processing_request(
                    text_content, selected_operation, question, options
                )
            except Exception as e:
                st.error(f"Invalid input: {e}")
                return

            # Process text with progress indicator
            with st.spinner("Processing your text..."):
                response = run_async(api_client.process_text(request))

            # Handle results
            handle_processing_result(response, selected_operation)

    with col2:
        # Usage guidance and tips
        display_usage_tips()

    # Results display section
    if 'last_response' in st.session_state and 'last_operation' in st.session_state:
        st.divider()
        display_results(st.session_state['last_response'], st.session_state['last_operation'])
        
        # Download functionality
        handle_results_download()


if __name__ == "__main__":
    # Handle example text loading from session state
    if 'example_text' in st.session_state:
        st.session_state['text_input'] = st.session_state['example_text']
        del st.session_state['example_text']

    # Launch main application
    main()
