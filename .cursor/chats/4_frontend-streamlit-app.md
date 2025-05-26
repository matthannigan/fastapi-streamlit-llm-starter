# Streamlit Interface and API Integration
_Exported on 5/25/2025 at 21:22:00 EDT from Cursor (0.50.7)_

---

**User**

**Objective:** Create an intuitive Streamlit interface with proper API integration.

---

**Cursor**

I'll help you create an intuitive Streamlit interface with proper API integration. Let me first explore the current project structure to understand what we're working with.

Let me check the current frontend structure:

Let me examine the current shared models to understand the data structures:

Now let me check the current frontend configuration:

Let me check the current app.py to see what's already implemented:

Let me check the utils directory to see what API client exists:

Now let me check the backend structure to understand the available endpoints:

Perfect! Now I have a good understanding of the current structure. Based on the attached plan and the existing code, I need to create an improved Streamlit interface that properly integrates with the backend API. Let me implement the enhanced frontend components:

## 1. First, let's update the frontend configuration to match the plan:

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Frontend application settings."""
    
    # API Configuration
    api_base_url: str = os.getenv("API_BASE_URL", "http://backend:8000")
    
    # UI Configuration
    page_title: str = "AI Text Processor"
    page_icon: str = "🤖"
    layout: str = "wide"
    
    # Features
    show_debug_info: bool = os.getenv("SHOW_DEBUG_INFO", "false").lower() == "true"
    max_text_length: int = int(os.getenv("MAX_TEXT_LENGTH", "10000"))
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## 2. Now let's create the enhanced API client:

```python
import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
import streamlit as st

from shared.models import (
    TextProcessingRequest, 
    TextProcessingResponse, 
    ProcessingOperation,
    ErrorResponse
)
from frontend.app.config import settings

logger = logging.getLogger(__name__)

class APIClient:
    """Client for communicating with the backend API."""
    
    def __init__(self):
        self.base_url = settings.api_base_url
        self.timeout = httpx.Timeout(60.0)  # 60 second timeout
    
    async def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def get_operations(self) -> Optional[Dict[str, Any]]:
        """Get available processing operations."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/operations")
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get operations: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error getting operations: {e}")
            return None
    
    async def process_text(self, request: TextProcessingRequest) -> Optional[TextProcessingResponse]:
        """Process text using the backend API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/process",
                    json=request.dict()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return TextProcessingResponse(**data)
                else:
                    error_data = response.json()
                    error_msg = error_data.get('detail', 'Unknown error')
                    logger.error(f"API error: {error_msg}")
                    st.error(f"API Error: {error_msg}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Request timeout")
            st.error("Request timed out. Please try again.")
            return None
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            st.error(f"Error: {str(e)}")
            return None

# Helper function for running async code in Streamlit
def run_async(coro):
    """Run async code in Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

# Global client instance
api_client = APIClient()
```

## 3. Now let's create the enhanced main Streamlit application:

```python
import streamlit as st
import asyncio
import json
from typing import Dict, Any, Optional

from shared.models import TextProcessingRequest, ProcessingOperation
from frontend.app.utils.api_client import api_client, run_async
from frontend.app.config import settings

# Configure Streamlit page
st.set_page_config(
    page_title=settings.page_title,
    page_icon=settings.page_icon,
    layout=settings.layout,
    initial_sidebar_state="expanded"
)

def display_header():
    """Display the application header."""
    st.title("🤖 AI Text Processor")
    st.markdown(
        "Process text using advanced AI models. Choose from summarization, "
        "sentiment analysis, key point extraction, and more!"
    )
    st.divider()

def check_api_health():
    """Check API health and display status."""
    with st.sidebar:
        st.subheader("🔧 System Status")
        
        # Check API health
        is_healthy = run_async(api_client.health_check())
        
        if is_healthy:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Unavailable")
            st.warning("Please ensure the backend service is running.")
            return False
        
        return True

def get_operation_info() -> Optional[Dict[str, Any]]:
    """Get operation information from API."""
    operations = run_async(api_client.get_operations())
    if operations:
        return {op['id']: op for op in operations['operations']}
    return None

def create_sidebar():
    """Create the sidebar with operation selection."""
    with st.sidebar:
        st.subheader("⚙️ Configuration")
        
        # Get available operations
        operations_info = get_operation_info()
        if not operations_info:
            st.error("Failed to load operations")
            return None, {}
        
        # Operation selection
        operation_options = {
            op_id: f"{info['name']} - {info['description']}"
            for op_id, info in operations_info.items()
        }
        
        selected_op = st.selectbox(
            "Choose Operation",
            options=list(operation_options.keys()),
            format_func=lambda x: operation_options[x],
            key="operation_select"
        )
        
        # Operation-specific options
        options = {}
        op_info = operations_info[selected_op]
        
        if "max_length" in op_info.get("options", []):
            options["max_length"] = st.slider(
                "Summary Length (words)",
                min_value=50,
                max_value=500,
                value=150,
                step=25
            )
        
        if "max_points" in op_info.get("options", []):
            options["max_points"] = st.slider(
                "Number of Key Points",
                min_value=3,
                max_value=10,
                value=5
            )
        
        if "num_questions" in op_info.get("options", []):
            options["num_questions"] = st.slider(
                "Number of Questions",
                min_value=3,
                max_value=10,
                value=5
            )
        
        return selected_op, options

def display_text_input() -> tuple[str, Optional[str]]:
    """Display text input area."""
    st.subheader("📝 Input Text")
    
    # Text input options
    input_method = st.radio(
        "Input Method",
        ["Type/Paste Text", "Upload File"],
        horizontal=True
    )
    
    text_content = ""
    
    if input_method == "Type/Paste Text":
        text_content = st.text_area(
            "Enter your text here:",
            height=200,
            max_chars=settings.max_text_length,
            placeholder="Paste or type the text you want to process...",
            value=st.session_state.get('text_input', '')
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload a text file",
            type=['txt', 'md'],
            help="Upload a .txt or .md file"
        )
        
        if uploaded_file is not None:
            try:
                text_content = str(uploaded_file.read(), "utf-8")
                st.success(f"File uploaded successfully! ({len(text_content)} characters)")
                
                # Show preview
                with st.expander("Preview uploaded text"):
                    st.text(text_content[:500] + "..." if len(text_content) > 500 else text_content)
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    # Question input for Q&A
    question = None
    if st.session_state.get("operation_select") == "qa":
        question = st.text_input(
            "Enter your question about the text:",
            placeholder="What is the main topic discussed in this text?"
        )
    
    return text_content, question

def display_results(response, operation: str):
    """Display processing results."""
    st.subheader("📊 Results")
    
    # Processing info
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
        
        # Color code sentiment
        color = {
            "positive": "green",
            "negative": "red",
            "neutral": "gray"
        }.get(sentiment.sentiment, "gray")
        
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
    
    # Debug information
    if settings.show_debug_info:
        with st.expander("🔍 Debug Information"):
            st.json(response.dict())

def main():
    """Main application function."""
    display_header()
    
    # Check API health
    if not check_api_health():
        st.stop()
    
    # Create sidebar
    selected_operation, options = create_sidebar()
    if not selected_operation:
        st.stop()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Text input
        text_content, question = display_text_input()
        
        # Process button
        if st.button("🚀 Process Text", type="primary", use_container_width=True):
            if not text_content.strip():
                st.error("Please enter some text to process.")
                return
            
            if selected_operation == "qa" and not question:
                st.error("Please enter a question for Q&A operation.")
                return
            
            # Create request
            request = TextProcessingRequest(
                text=text_content,
                operation=ProcessingOperation(selected_operation),
                question=question,
                options=options
            )
            
            # Process text with progress indicator
            with st.spinner("Processing your text..."):
                response = run_async(api_client.process_text(request))
            
            if response and response.success:
                # Store results in session state
                st.session_state['last_response'] = response
                st.session_state['last_operation'] = selected_operation
                st.success("✅ Processing completed!")
            else:
                st.error("❌ Processing failed. Please try again.")
    
    with col2:
        # Tips and information
        st.subheader("💡 Tips")
        st.markdown("""
        **For best results:**
        - Use clear, well-structured text
        - Longer texts work better for summarization
        - Be specific with your questions for Q&A
        - Try different operations to explore your text
        """)
        
        # Example texts
        with st.expander("📚 Example Texts"):
            if st.button("Load News Article Example"):
                example_text = """
                Artificial intelligence is rapidly transforming industries across the globe. 
                From healthcare to finance, AI technologies are enabling unprecedented 
                automation and decision-making capabilities. Machine learning algorithms 
                can now process vast amounts of data in seconds, identifying patterns 
                that would take humans hours or days to discover. However, this rapid 
                advancement also raises important questions about job displacement, 
                privacy, and the ethical implications of automated decision-making. 
                As we move forward, it will be crucial to balance innovation with 
                responsible development and deployment of AI systems.
                """
                st.session_state['text_input'] = example_text
                st.rerun()
    
    # Display results if available
    if 'last_response' in st.session_state and 'last_operation' in st.session_state:
        st.divider()
        display_results(st.session_state['last_response'], st.session_state['last_operation'])
        
        # Download results
        if st.button("📥 Download Results"):
            results_json = json.dumps(st.session_state['last_response'].dict(), indent=2)
            st.download_button(
                label="Download as JSON",
                data=results_json,
                file_name=f"ai_text_processing_results_{st.session_state['last_operation']}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    # Load example text if set
    if 'example_text' in st.session_state:
        st.session_state['text_input'] = st.session_state['example_text']
        del st.session_state['example_text']
    
    main()
```

## 4. Now let's update the frontend requirements to include the necessary dependencies:

```pip-requirements
streamlit==1.28.1
httpx==0.25.0
pydantic-settings==2.0.3
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
```

## 5. Let's update the Dockerfile to match the enhanced version from the plan:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Add shared models to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health

# Run the application
CMD ["streamlit", "run", "app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
```

## 6. Let's create a symlink to the shared models so the frontend can access them:

## 7. Let's test the application by running it:

Let me check if there are any issues with the docker-compose setup:

I need to update the docker-compose to use the correct API_BASE_URL environment variable:

```dockercompose
  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      - FRONTEND_PORT=8501
    env_file:
      - .env

->

  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      - FRONTEND_PORT=8501
      - API_BASE_URL=http://backend:8000
    env_file:
      - .env
```

Now let me check the logs to see if there are any issues:

Great! The frontend is running. Let me also check the backend logs:

I see the issue. The backend has import errors because it's trying to import from `backend.app.config` but the module path is incorrect in the Docker container. Let me fix the backend imports first:



Now let me fix the backend imports. The issue is that the backend is trying to import from `backend.app.config` but in the Docker container, the path should be `app.config`:

```python
from backend.app.config import settings
from backend.app.services.text_processor import text_processor

->

from app.config import settings
from app.services.text_processor import text_processor
```

Now let me check if there are any other backend files that need import fixes:

Let me fix the text_processor import:

```python
from backend.app.config import settings

->

from app.config import settings
```

Now let's try running the application again:

Let me check the status of the containers:

Let me check the logs to see what's happening:

Let me try starting the containers again:

Great! Now let me check the status:

Perfect! Both containers are running and healthy. Let me check the logs to make sure everything is working:

Excellent! Both services are running properly. Let me test the API endpoints to make sure they're working:

Perfect! Now let me create a simple README to document the enhanced Streamlit interface:

```markdown
# Enhanced Streamlit Frontend

This is an intuitive Streamlit interface for the AI Text Processor API with proper API integration and modern UI components.

## Features

### 🎯 Core Functionality
- **Multiple Text Processing Operations**: Summarization, sentiment analysis, key point extraction, question generation, and Q&A
- **Dynamic Operation Selection**: Choose from available operations with operation-specific options
- **Real-time API Integration**: Seamless communication with the FastAPI backend
- **File Upload Support**: Upload `.txt` and `.md` files for processing
- **Results Download**: Export processing results as JSON

### 🎨 User Interface
- **Clean, Modern Design**: Intuitive layout with clear navigation
- **Responsive Layout**: Works well on different screen sizes
- **Real-time Status**: API health monitoring and connection status
- **Progress Indicators**: Visual feedback during text processing
- **Error Handling**: Clear error messages and user guidance

### ⚙️ Configuration Options
- **Operation-Specific Settings**: 
  - Summary length control (50-500 words)
  - Number of key points (3-10)
  - Number of questions (3-10)
- **Input Methods**: Type/paste text or upload files
- **Debug Mode**: Optional debug information display

## Usage

### Starting the Application
```bash
docker-compose up --build
```

The Streamlit interface will be available at: http://localhost:8501

### Using the Interface

1. **Check API Status**: The sidebar shows the backend connection status
2. **Select Operation**: Choose from available text processing operations
3. **Configure Options**: Adjust operation-specific settings in the sidebar
4. **Input Text**: Either type/paste text or upload a file
5. **Process**: Click "Process Text" to send the request to the API
6. **View Results**: Results are displayed with operation-specific formatting
7. **Download**: Export results as JSON for further use

### Available Operations

- **Summarize**: Generate concise summaries with configurable length
- **Sentiment Analysis**: Analyze emotional tone with confidence scores
- **Key Points**: Extract main points with configurable count
- **Generate Questions**: Create questions about the text content
- **Q&A**: Answer specific questions about the text

## API Integration

The frontend integrates with the FastAPI backend through:

- **Health Checks**: Monitors backend availability
- **Operations Discovery**: Dynamically loads available operations
- **Text Processing**: Sends requests using shared Pydantic models
- **Error Handling**: Graceful handling of API errors and timeouts

## Configuration

Environment variables:
- `API_BASE_URL`: Backend API URL (default: http://backend:8000)
- `SHOW_DEBUG_INFO`: Enable debug information (default: false)
- `MAX_TEXT_LENGTH`: Maximum text input length (default: 10000)

## Development

### Local Development
```bash
cd frontend
pip install -r requirements.txt
streamlit run app/app.py
```

### Docker Development
```bash
docker-compose up --build frontend
```

## Architecture

```
frontend/
├── app/
│   ├── app.py              # Main Streamlit application
│   ├── config.py           # Configuration settings
│   └── utils/
│       └── api_client.py   # API client for backend communication
├── shared/                 # Symlink to shared models
├── requirements.txt        # Python dependencies
└── Dockerfile             # Container configuration
```

## Features in Detail

### Dynamic UI Components
- Operation selection with descriptions
- Conditional input fields (Q&A questions)
- Progress indicators and status messages
- Responsive column layouts

### Error Handling
- Connection status monitoring
- Timeout handling with user feedback
- Validation error display
- Graceful degradation when API is unavailable

### Results Display
- Operation-specific result formatting
- Sentiment analysis with color coding
- Numbered lists for key points and questions
- Processing metrics and metadata

### File Upload
- Support for text and markdown files
- File preview functionality
- Character count and validation
- Error handling for file reading

This enhanced frontend provides a professional, user-friendly interface for interacting with the AI text processing capabilities while maintaining clean code architecture and proper error handling.
```

Now let me test the frontend by accessing it through the browser. Let me check if we can access the Streamlit interface:

Perfect! Let me also create a simple test to verify the frontend can communicate with the backend:

```python
#!/usr/bin/env python3
"""
Simple integration test to verify frontend-backend communication.
"""

import asyncio
import sys
import httpx
from shared.models import TextProcessingRequest, ProcessingOperation

async def test_integration():
    """Test the integration between frontend and backend."""
    
    print("🧪 Testing FastAPI-Streamlit Integration...")
    
    # Test backend health
    print("\n1. Testing backend health...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ Backend health check passed")
                health_data = response.json()
                print(f"   Status: {health_data['status']}")
                print(f"   AI Model Available: {health_data['ai_model_available']}")
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Test operations endpoint
    print("\n2. Testing operations endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/operations")
            if response.status_code == 200:
                print("✅ Operations endpoint working")
                ops_data = response.json()
                print(f"   Available operations: {len(ops_data['operations'])}")
                for op in ops_data['operations']:
                    print(f"   - {op['name']}: {op['description']}")
            else:
                print(f"❌ Operations endpoint failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Operations endpoint failed: {e}")
        return False
    
    # Test text processing
    print("\n3. Testing text processing...")
    try:
        request = TextProcessingRequest(
            text="This is a test text for integration testing. It should be processed successfully by the AI model.",
            operation=ProcessingOperation.SUMMARIZE,
            options={"max_length": 50}
        )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/process",
                json=request.dict()
            )
            if response.status_code == 200:
                print("✅ Text processing successful")
                result = response.json()
                print(f"   Operation: {result['operation']}")
                print(f"   Success: {result['success']}")
                if result.get('result'):
                    print(f"   Result: {result['result'][:100]}...")
            else:
                print(f"❌ Text processing failed: {response.status_code}")
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                return False
    except Exception as e:
        print(f"❌ Text processing failed: {e}")
        return False
    
    # Test Streamlit health
    print("\n4. Testing Streamlit frontend...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8501/_stcore/health")
            if response.status_code == 200:
                print("✅ Streamlit frontend accessible")
            else:
                print(f"❌ Streamlit frontend failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Streamlit frontend failed: {e}")
        return False
    
    print("\n🎉 All integration tests passed!")
    print("\n📱 Access the application:")
    print("   Frontend (Streamlit): http://localhost:8501")
    print("   Backend (FastAPI):    http://localhost:8000")
    print("   API Docs:             http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1)
```

Now let me run the integration test:

Let me install the required dependencies and run the test:

Let me run the test inside the Docker container instead:

Perfect! Let me create a summary of what we've accomplished:

## ✅ **Successfully Created an Intuitive Streamlit Interface with Proper API Integration**

### 🎯 **What We've Built:**

1. **Enhanced Frontend Configuration** (`frontend/app/config.py`)
   - Uses `pydantic_settings` for robust configuration management
   - Configurable API base URL, UI settings, and feature flags
   - Environment variable support for different deployment scenarios

2. **Robust API Client** (`frontend/app/utils/api_client.py`)
   - Async HTTP client with proper timeout handling
   - Integration with shared Pydantic models for type safety
   - Comprehensive error handling with user-friendly messages
   - Health checks and operations discovery

3. **Modern Streamlit Interface** (`frontend/app/app.py`)
   - **Dynamic Operation Selection**: Automatically loads available operations from the API
   - **Operation-Specific Options**: Configurable sliders for summary length, key points count, etc.
   - **Multiple Input Methods**: Text area input and file upload support
   - **Real-time Status Monitoring**: API health checks with visual indicators
   - **Professional Results Display**: Operation-specific formatting with metrics
   - **Download Functionality**: Export results as JSON
   - **Error Handling**: Graceful degradation when API is unavailable

4. **Enhanced Docker Configuration**
   - Updated Dockerfile with health checks and proper Python path setup
   - Improved docker-compose with correct environment variables
   - Symlinked shared models for seamless integration

### 🎨 **Key Features:**

#### **User Interface**
- Clean, modern design with intuitive navigation
- Responsive layout with sidebar configuration
- Progress indicators and status messages
- Color-coded sentiment analysis results
- Numbered lists for key points and questions

#### **API Integration**
- Seamless communication with FastAPI backend
- Dynamic operation discovery from `/operations` endpoint
- Proper request/response handling using shared models
- Timeout handling and connection monitoring

#### **Configuration & Flexibility**
- Environment-based configuration
- Debug mode for development
- Configurable text length limits
- Operation-specific parameter controls

#### **Error Handling**
- Connection status monitoring
- Timeout handling with user feedback
- Validation error display
- Graceful degradation when services are unavailable

### 🚀 **Current Status:**

✅ **Backend**: Running healthy on port 8000  
✅ **Frontend**: Running healthy on port 8501  
✅ **API Endpoints**: All endpoints responding correctly  
✅ **Integration**: Frontend successfully communicates with backend  

### 📱 **Access Points:**

- **Streamlit Interface**: http://localhost:8501
- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 🔧 **Available Operations:**

1. **Summarize** - Generate concise summaries (configurable length: 50-500 words)
2. **Sentiment Analysis** - Analyze emotional tone with confidence scores
3. **Key Points** - Extract main points (configurable count: 3-10)
4. **Generate Questions** - Create questions about content (configurable count: 3-10)
5. **Q&A** - Answer specific questions about the text

### 📁 **Enhanced Architecture:**

```
frontend/
├── app/
│   ├── app.py              # Main Streamlit application
│   ├── config.py           # Pydantic settings configuration
│   └── utils/
│       └── api_client.py   # Async API client with error handling
├── shared/                 # Symlink to shared Pydantic models
├── requirements.txt        # Updated dependencies
├── Dockerfile             # Enhanced with health checks
└── README.md              # Comprehensive documentation
```

The enhanced Streamlit interface now provides a professional, user-friendly experience with proper API integration, comprehensive error handling, and modern UI components. Users can easily select operations, configure parameters, input text through multiple methods, and view beautifully formatted results with the ability to download them for further use.

```plaintext
frontend/
├── app/
│   ├── app.py              # Main Streamlit application
│   ├── config.py           # Pydantic settings configuration
│   └── utils/
│       └── api_client.py   # Async API client with error handling
├── shared/                 # Symlink to shared Pydantic models
├── requirements.txt        # Updated dependencies
├── Dockerfile             # Enhanced with health checks
└── README.md              # Comprehensive documentation
```

