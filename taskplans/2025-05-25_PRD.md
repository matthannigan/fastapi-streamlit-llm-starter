# FastAPI-Streamlit-LLM Starter Template Prompt Plan

## Overview

This prompt plan creates a production-ready starter template demonstrating the integration of FastAPI, Streamlit, and PydanticAI for building LLM-powered applications. The example application is an "AI Text Processor" that can perform multiple text analysis operations.

## Example Application: AI Text Processor

**Features:**
- Text summarization
- Sentiment analysis
- Key point extraction
- Question generation
- Simple Q&A about text content

**Architecture:**
- Frontend: Streamlit UI with form handling and results display
- Backend: FastAPI REST API with async processing
- AI Integration: PydanticAI with configurable models
- Shared: Pydantic models for type safety and validation
- Infrastructure: Docker containerization for easy deployment

---

## Prompt 1: Project Structure & Foundation

**Objective:** Create the complete directory structure, configuration files, and foundational setup.

### Create the following project structure:

```
fastapi-streamlit-llm-starter/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── text_processor.py
├── frontend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       └── utils/
│           ├── __init__.py
│           └── api_client.py
└── shared/
    ├── __init__.py
    └── models.py
```

### Files to create:

**`.env.example`:**
```env
# AI Model Configuration
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.7

# API Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=8501

# Development Settings
DEBUG=true
LOG_LEVEL=INFO

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:8501"]
```

**`.gitignore`:**
```gitignore
# Environment files
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Docker
.dockerignore

# OS
.DS_Store
Thumbs.db
```

**Requirements files:**

`backend/requirements.txt`:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.4.2
pydantic-ai==0.0.8
python-multipart==0.0.6
python-dotenv==1.0.0
httpx==0.25.0
```

`frontend/requirements.txt`:
```txt
streamlit==1.28.1
httpx==0.25.0
python-dotenv==1.0.0
```

### Key Requirements:
- Include proper Python package structure with `__init__.py` files
- Environment-based configuration with secure defaults
- Clear separation between backend, frontend, and shared components
- Production-ready `.gitignore` and environment setup

---

## Prompt 2: Shared Data Models

**Objective:** Create comprehensive Pydantic models for type safety and API consistency.

### Create `shared/models.py`:

```python
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

class ProcessingOperation(str, Enum):
    """Available text processing operations."""
    SUMMARIZE = "summarize"
    SENTIMENT = "sentiment"
    KEY_POINTS = "key_points"
    QUESTIONS = "questions"
    QA = "qa"

class TextProcessingRequest(BaseModel):
    """Request model for text processing operations."""
    text: str = Field(..., min_length=10, max_length=10000, description="Text to process")
    operation: ProcessingOperation = Field(..., description="Type of processing to perform")
    question: Optional[str] = Field(None, description="Question for Q&A operation")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Operation-specific options")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Artificial intelligence is transforming how we work...",
                "operation": "summarize",
                "options": {"max_length": 100}
            }
        }

class SentimentResult(BaseModel):
    """Result model for sentiment analysis."""
    sentiment: str = Field(..., description="Overall sentiment (positive/negative/neutral)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    explanation: str = Field(..., description="Brief explanation of the sentiment")

class TextProcessingResponse(BaseModel):
    """Response model for text processing results."""
    operation: ProcessingOperation
    success: bool = True
    result: Optional[str] = None
    sentiment: Optional[SentimentResult] = None
    key_points: Optional[List[str]] = None
    questions: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation": "summarize",
                "success": True,
                "result": "This text discusses the impact of artificial intelligence...",
                "metadata": {"word_count": 150},
                "processing_time": 2.3
            }
        }

class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    ai_model_available: bool = True
```

### Key Features:
- Comprehensive type definitions with validation rules
- Enum for operation types to prevent invalid values
- Nested models for complex responses (sentiment analysis)
- Example schemas for API documentation
- Error handling models
- Flexible options field for operation-specific parameters

---

## Prompt 3: Backend API Implementation

**Objective:** Create a robust FastAPI application with PydanticAI integration.

### Create `backend/app/config.py`:

```python
import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # AI Configuration
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "gemini-2.0-flash-exp")
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    
    # API Configuration
    host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    port: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # CORS Configuration
    allowed_origins: List[str] = ["http://localhost:8501", "http://frontend:8501"]
    
    # Application Settings
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Create `backend/app/services/text_processor.py`:

```python
import asyncio
import time
from typing import Dict, Any, List
import logging
from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName

from shared.models import (
    ProcessingOperation, 
    TextProcessingRequest, 
    TextProcessingResponse,
    SentimentResult
)
from backend.app.config import settings

logger = logging.getLogger(__name__)

class TextProcessorService:
    """Service for processing text using AI models."""
    
    def __init__(self):
        """Initialize the text processor with AI agent."""
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        self.agent = Agent(
            model=settings.ai_model,
            system_prompt="You are a helpful AI assistant specialized in text analysis.",
        )
    
    async def process_text(self, request: TextProcessingRequest) -> TextProcessingResponse:
        """Process text based on the requested operation."""
        start_time = time.time()
        
        try:
            logger.info(f"Processing text with operation: {request.operation}")
            
            # Route to specific processing method
            if request.operation == ProcessingOperation.SUMMARIZE:
                result = await self._summarize_text(request.text, request.options)
            elif request.operation == ProcessingOperation.SENTIMENT:
                result = await self._analyze_sentiment(request.text)
            elif request.operation == ProcessingOperation.KEY_POINTS:
                result = await self._extract_key_points(request.text, request.options)
            elif request.operation == ProcessingOperation.QUESTIONS:
                result = await self._generate_questions(request.text, request.options)
            elif request.operation == ProcessingOperation.QA:
                result = await self._answer_question(request.text, request.question)
            else:
                raise ValueError(f"Unsupported operation: {request.operation}")
            
            processing_time = time.time() - start_time
            
            # Create response with timing metadata
            response = TextProcessingResponse(
                operation=request.operation,
                processing_time=processing_time,
                metadata={"word_count": len(request.text.split())}
            )
            
            # Set result based on operation type
            if request.operation == ProcessingOperation.SENTIMENT:
                response.sentiment = result
            elif request.operation == ProcessingOperation.KEY_POINTS:
                response.key_points = result
            elif request.operation == ProcessingOperation.QUESTIONS:
                response.questions = result
            else:
                response.result = result
                
            logger.info(f"Processing completed in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise
    
    async def _summarize_text(self, text: str, options: Dict[str, Any]) -> str:
        """Summarize the provided text."""
        max_length = options.get("max_length", 100)
        
        prompt = f"""
        Please provide a concise summary of the following text in approximately {max_length} words:
        
        Text: {text}
        
        Summary:
        """
        
        result = await self.agent.run(prompt)
        return result.data.strip()
    
    async def _analyze_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment of the provided text."""
        prompt = f"""
        Analyze the sentiment of the following text. Respond with a JSON object containing:
        - sentiment: "positive", "negative", or "neutral"
        - confidence: a number between 0.0 and 1.0
        - explanation: a brief explanation of the sentiment
        
        Text: {text}
        
        Response (JSON only):
        """
        
        result = await self.agent.run(prompt)
        
        # Parse the JSON response
        import json
        try:
            sentiment_data = json.loads(result.data.strip())
            return SentimentResult(**sentiment_data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse sentiment JSON: {e}")
            # Fallback response
            return SentimentResult(
                sentiment="neutral",
                confidence=0.5,
                explanation="Unable to analyze sentiment accurately"
            )
    
    async def _extract_key_points(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Extract key points from the text."""
        max_points = options.get("max_points", 5)
        
        prompt = f"""
        Extract the {max_points} most important key points from the following text.
        Return each point as a separate line starting with a dash (-).
        
        Text: {text}
        
        Key Points:
        """
        
        result = await self.agent.run(prompt)
        
        # Parse the response into a list
        points = []
        for line in result.data.strip().split('\n'):
            line = line.strip()
            if line.startswith('-'):
                points.append(line[1:].strip())
            elif line and not line.startswith('Key Points:'):
                points.append(line)
        
        return points[:max_points]
    
    async def _generate_questions(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Generate questions about the text."""
        num_questions = options.get("num_questions", 5)
        
        prompt = f"""
        Generate {num_questions} thoughtful questions about the following text.
        These questions should help someone better understand or think more deeply about the content.
        Return each question on a separate line.
        
        Text: {text}
        
        Questions:
        """
        
        result = await self.agent.run(prompt)
        
        # Parse questions into a list
        questions = []
        for line in result.data.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('Questions:'):
                # Remove numbering if present
                if line[0].isdigit() and '.' in line[:5]:
                    line = line.split('.', 1)[1].strip()
                questions.append(line)
        
        return questions[:num_questions]
    
    async def _answer_question(self, text: str, question: str) -> str:
        """Answer a question about the text."""
        if not question:
            raise ValueError("Question is required for Q&A operation")
        
        prompt = f"""
        Based on the following text, please answer this question:
        
        Question: {question}
        
        Text: {text}
        
        Answer:
        """
        
        result = await self.agent.run(prompt)
        return result.data.strip()

# Global service instance
text_processor = TextProcessorService()
```

### Create `backend/app/main.py`:

```python
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.models import (
    TextProcessingRequest, 
    TextProcessingResponse, 
    ErrorResponse,
    HealthResponse
)
from backend.app.config import settings
from backend.app.services.text_processor import text_processor

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting FastAPI application")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"AI Model: {settings.ai_model}")
    yield
    logger.info("Shutting down FastAPI application")

# Create FastAPI application
app = FastAPI(
    title="AI Text Processor API",
    description="API for processing text using AI models",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        ai_model_available=bool(settings.gemini_api_key)
    )

@app.post("/process", response_model=TextProcessingResponse)
async def process_text(request: TextProcessingRequest):
    """Process text using AI models."""
    try:
        logger.info(f"Received request for operation: {request.operation}")
        
        # Validate Q&A request
        if request.operation.value == "qa" and not request.question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question is required for Q&A operation"
            )
        
        # Process the text
        result = await text_processor.process_text(request)
        
        logger.info("Request processed successfully")
        return result
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process text"
        )

@app.get("/operations")
async def get_operations():
    """Get available processing operations."""
    return {
        "operations": [
            {
                "id": "summarize",
                "name": "Summarize",
                "description": "Generate a concise summary of the text",
                "options": ["max_length"]
            },
            {
                "id": "sentiment",
                "name": "Sentiment Analysis",
                "description": "Analyze the emotional tone of the text",
                "options": []
            },
            {
                "id": "key_points",
                "name": "Key Points",
                "description": "Extract the main points from the text",
                "options": ["max_points"]
            },
            {
                "id": "questions",
                "name": "Generate Questions",
                "description": "Create questions about the text content",
                "options": ["num_questions"]
            },
            {
                "id": "qa",
                "name": "Question & Answer",
                "description": "Answer a specific question about the text",
                "options": [],
                "requires_question": True
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
```

### Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Add shared models to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Key Features:
- Robust error handling and logging
- Environment-based configuration
- Type-safe request/response handling
- Comprehensive AI service with multiple operations
- Health checks and monitoring endpoints
- CORS configuration for frontend integration
- Docker-ready with health checks

---

## Prompt 4: Frontend Streamlit Application

**Objective:** Create an intuitive Streamlit interface with proper API integration.

### Create `frontend/app/config.py`:

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

### Create `frontend/app/utils/api_client.py`:

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

### Create `frontend/app/app.py`:

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
            placeholder="Paste or type the text you want to process..."
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
                st.session_state['example_text'] = example_text
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

### Create `frontend/Dockerfile`:

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

### Key Features:
- Intuitive multi-step interface
- Real-time API health monitoring
- File upload and text input support
- Operation-specific configuration options
- Rich result display with formatting
- Progress indicators and error handling
- Debug mode for development
- Example content for testing

---

## Prompt 5: Docker Configuration

**Objective:** Create comprehensive Docker setup for development and production deployment.

### Create root-level `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ai-text-processor-backend
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - AI_MODEL=${AI_MODEL:-gemini-2.0-flash-exp}
      - AI_TEMPERATURE=${AI_TEMPERATURE:-0.7}
      - DEBUG=${DEBUG:-true}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - ALLOWED_ORIGINS=["http://localhost:8501", "http://frontend:8501"]
    volumes:
      - ./backend:/app
      - ./shared:/app/shared
    networks:
      - ai-processor-network
    restart: unless-stopped
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ai-text-processor-frontend
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://backend:8000
      - SHOW_DEBUG_INFO=${SHOW_DEBUG_INFO:-false}
      - MAX_TEXT_LENGTH=${MAX_TEXT_LENGTH:-10000}
    volumes:
      - ./frontend:/app
      - ./shared:/app/shared
    networks:
      - ai-processor-network
    restart: unless-stopped
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    container_name: ai-text-processor-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - ai-processor-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: ai-text-processor-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - ai-processor-network
    restart: unless-stopped
    depends_on:
      - backend
      - frontend

volumes:
  redis_data:

networks:
  ai-processor-network:
    driver: bridge
```

### Create `docker-compose.dev.yml` for development:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./backend:/app
      - ./shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    environment:
      - SHOW_DEBUG_INFO=true
    volumes:
      - ./frontend:/app
      - ./shared:/app/shared
    command: streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501 --server.runOnSave true

  # Remove production services for development
  nginx: null
```

### Create `docker-compose.prod.yml` for production:

```yaml
version: '3.8'

services:
  backend:
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
    volumes: []  # No volume mounts in production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  frontend:
    environment:
      - SHOW_DEBUG_INFO=false
    volumes: []  # No volume mounts in production
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:8501;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=frontend:10m rate=30r/s;

    server {
        listen 80;
        server_name localhost;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # Frontend
        location / {
            limit_req zone=frontend burst=20 nodelay;
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support for Streamlit
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Backend API
        location /api/ {
            limit_req zone=api burst=5 nodelay;
            rewrite ^/api/(.*)$ /$1 break;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health checks
        location /health {
            access_log off;
            proxy_pass http://backend/health;
        }
    }
}
```

### Create `Makefile` for easy management:

```makefile
.PHONY: help build up down logs clean dev prod test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs for all services
	docker-compose logs -f

clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

dev: ## Start development environment
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

prod: ## Start production environment
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

test: ## Run tests
	docker-compose exec backend python -m pytest tests/
	docker-compose exec frontend python -m pytest tests/

restart: ## Restart all services
	docker-compose restart

backend-shell: ## Get shell access to backend container
	docker-compose exec backend /bin/bash

frontend-shell: ## Get shell access to frontend container
	docker-compose exec frontend /bin/bash

backend-logs: ## Show backend logs
	docker-compose logs -f backend

frontend-logs: ## Show frontend logs
	docker-compose logs -f frontend
```

### Key Features:
- Multi-environment support (dev/prod)
- Load balancing and scaling ready
- Health checks for all services
- Redis for caching/sessions
- Nginx reverse proxy with rate limiting
- Volume management for development
- Easy management with Makefile
- Security headers and best practices

---

## Prompt 6: Testing Setup

**Objective:** Create comprehensive test suite for both backend and frontend components.

### Create `backend/tests/` structure:

```
backend/tests/
├── __init__.py
├── conftest.py
├── test_main.py
├── test_text_processor.py
└── test_models.py
```

### Create `backend/tests/conftest.py`:

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

from backend.app.main import app
from shared.models import TextProcessingRequest, ProcessingOperation

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    Artificial intelligence (AI) is intelligence demonstrated by machines, 
    in contrast to the natural intelligence displayed by humans and animals. 
    Leading AI textbooks define the field as the study of "intelligent agents": 
    any device that perceives its environment and takes actions that maximize 
    its chance of successfully achieving its goals.
    """

@pytest.fixture
def sample_request(sample_text):
    """Sample request for testing."""
    return TextProcessingRequest(
        text=sample_text,
        operation=ProcessingOperation.SUMMARIZE,
        options={"max_length": 100}
    )

@pytest.fixture
def mock_ai_response():
    """Mock AI response for testing."""
    return AsyncMock(return_value=AsyncMock(data="This is a test summary."))

@pytest.fixture(autouse=True)
def mock_ai_agent():
    """Mock the AI agent to avoid actual API calls during testing."""
    with patch('backend.app.services.text_processor.Agent') as mock:
        mock_instance = AsyncMock()
        mock_instance.run = AsyncMock(return_value=AsyncMock(data="Mock AI response"))
        mock.return_value = mock_instance
        yield mock_instance
```

### Create `backend/tests/test_main.py`:

```python
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.app.main import app
from shared.models import ProcessingOperation

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client: TestClient):
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "ai_model_available" in data

class TestOperationsEndpoint:
    """Test operations endpoint."""
    
    def test_get_operations(self, client: TestClient):
        """Test getting available operations."""
        response = client.get("/operations")
        assert response.status_code == 200
        
        data = response.json()
        assert "operations" in data
        assert len(data["operations"]) > 0
        
        # Check first operation structure
        op = data["operations"][0]
        assert "id" in op
        assert "name" in op
        assert "description" in op
        assert "options" in op

class TestProcessEndpoint:
    """Test text processing endpoint."""
    
    def test_process_summarize(self, client: TestClient, sample_text):
        """Test text summarization."""
        request_data = {
            "text": sample_text,
            "operation": "summarize",
            "options": {"max_length": 100}
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["operation"] == "summarize"
        assert "result" in data
        assert "processing_time" in data
        assert "timestamp" in data
    
    def test_process_sentiment(self, client: TestClient, sample_text):
        """Test sentiment analysis."""
        request_data = {
            "text": sample_text,
            "operation": "sentiment"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["operation"] == "sentiment"
        assert "sentiment" in data
    
    def test_process_qa_without_question(self, client: TestClient, sample_text):
        """Test Q&A without question returns error."""
        request_data = {
            "text": sample_text,
            "operation": "qa"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 400
    
    def test_process_qa_with_question(self, client: TestClient, sample_text):
        """Test Q&A with question."""
        request_data = {
            "text": sample_text,
            "operation": "qa",
            "question": "What is artificial intelligence?"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["operation"] == "qa"
        assert "result" in data
    
    def test_process_invalid_operation(self, client: TestClient, sample_text):
        """Test invalid operation returns error."""
        request_data = {
            "text": sample_text,
            "operation": "invalid_operation"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_process_empty_text(self, client: TestClient):
        """Test empty text returns validation error."""
        request_data = {
            "text": "",
            "operation": "summarize"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 422
    
    def test_process_text_too_long(self, client: TestClient):
        """Test text too long returns validation error."""
        long_text = "A" * 15000  # Exceeds max length
        request_data = {
            "text": long_text,
            "operation": "summarize"
        }
        
        response = client.post("/process", json=request_data)
        assert response.status_code == 422

class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are set correctly."""
        response = client.options("/health")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

class TestErrorHandling:
    """Test error handling."""
    
    def test_404_endpoint(self, client: TestClient):
        """Test 404 for non-existent endpoint."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
```

### Create `backend/tests/test_text_processor.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
import json

from backend.app.services.text_processor import TextProcessorService
from shared.models import TextProcessingRequest, ProcessingOperation, SentimentResult

class TestTextProcessorService:
    """Test the TextProcessorService class."""
    
    @pytest.fixture
    def service(self, mock_ai_agent):
        """Create a TextProcessorService instance."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            return TextProcessorService()
    
    async def test_summarize_text(self, service, sample_text):
        """Test text summarization."""
        # Mock AI response
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data="This is a test summary of artificial intelligence.")
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.SUMMARIZE,
            options={"max_length": 100}
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.operation == ProcessingOperation.SUMMARIZE
        assert response.result is not None
        assert response.processing_time is not None
        assert response.metadata["word_count"] > 0
    
    async def test_sentiment_analysis(self, service, sample_text):
        """Test sentiment analysis."""
        # Mock AI response with JSON
        sentiment_json = {
            "sentiment": "neutral",
            "confidence": 0.8,
            "explanation": "The text is informational and neutral in tone."
        }
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data=json.dumps(sentiment_json))
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.SENTIMENT
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.operation == ProcessingOperation.SENTIMENT
        assert response.sentiment is not None
        assert response.sentiment.sentiment == "neutral"
        assert response.sentiment.confidence == 0.8
    
    async def test_sentiment_analysis_invalid_json(self, service, sample_text):
        """Test sentiment analysis with invalid JSON response."""
        # Mock AI response with invalid JSON
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data="Not valid JSON")
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.SENTIMENT
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.sentiment.sentiment == "neutral"
        assert response.sentiment.confidence == 0.5
    
    async def test_key_points_extraction(self, service, sample_text):
        """Test key points extraction."""
        # Mock AI response
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data="""
            - AI is intelligence demonstrated by machines
            - Contrasts with natural intelligence of humans and animals
            - Focuses on intelligent agents and goal achievement
            """)
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.KEY_POINTS,
            options={"max_points": 3}
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.operation == ProcessingOperation.KEY_POINTS
        assert len(response.key_points) <= 3
        assert all(isinstance(point, str) for point in response.key_points)
    
    async def test_question_generation(self, service, sample_text):
        """Test question generation."""
        # Mock AI response
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data="""
            1. What is artificial intelligence?
            2. How does AI differ from natural intelligence?
            3. What are intelligent agents?
            """)
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.QUESTIONS,
            options={"num_questions": 3}
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.operation == ProcessingOperation.QUESTIONS
        assert len(response.questions) <= 3
        assert all("?" in question for question in response.questions)
    
    async def test_qa_processing(self, service, sample_text):
        """Test Q&A processing."""
        # Mock AI response
        service.agent.run = AsyncMock(
            return_value=AsyncMock(data="Artificial intelligence is intelligence demonstrated by machines.")
        )
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.QA,
            question="What is artificial intelligence?"
        )
        
        response = await service.process_text(request)
        
        assert response.success is True
        assert response.operation == ProcessingOperation.QA
        assert response.result is not None
    
    async def test_qa_without_question(self, service, sample_text):
        """Test Q&A without question raises error."""
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.QA
        )
        
        with pytest.raises(ValueError, match="Question is required"):
            await service.process_text(request)
    
    async def test_unsupported_operation(self, service, sample_text):
        """Test unsupported operation raises error."""
        # Create request with invalid operation (bypass enum validation)
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.SUMMARIZE  # Will be modified
        )
        request.operation = "unsupported_operation"
        
        with pytest.raises(ValueError, match="Unsupported operation"):
            await service.process_text(request)
    
    async def test_ai_error_handling(self, service, sample_text):
        """Test handling of AI service errors."""
        # Mock AI service to raise an exception
        service.agent.run = AsyncMock(side_effect=Exception("AI service error"))
        
        request = TextProcessingRequest(
            text=sample_text,
            operation=ProcessingOperation.SUMMARIZE
        )
        
        with pytest.raises(Exception):
            await service.process_text(request)

class TestServiceInitialization:
    """Test service initialization."""
    
    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                TextProcessorService()
    
    def test_initialization_with_api_key(self, mock_ai_agent):
        """Test successful initialization with API key."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            service = TextProcessorService()
            assert service.agent is not None
```

### Create `backend/tests/test_models.py`:

```python
import pytest
from datetime import datetime
from pydantic import ValidationError

from shared.models import (
    TextProcessingRequest,
    TextProcessingResponse,
    ProcessingOperation,
    SentimentResult,
    ErrorResponse,
    HealthResponse
)

class TestTextProcessingRequest:
    """Test TextProcessingRequest model."""
    
    def test_valid_request(self):
        """Test valid request creation."""
        request = TextProcessingRequest(
            text="This is a test text for processing.",
            operation=ProcessingOperation.SUMMARIZE,
            options={"max_length": 100}
        )
        
        assert request.text == "This is a test text for processing."
        assert request.operation == ProcessingOperation.SUMMARIZE
        assert request.options == {"max_length": 100}
        assert request.question is None
    
    def test_qa_request_with_question(self):
        """Test Q&A request with question."""
        request = TextProcessingRequest(
            text="Sample text",
            operation=ProcessingOperation.QA,
            question="What is this about?"
        )
        
        assert request.question == "What is this about?"
    
    def test_text_too_short(self):
        """Test validation fails for text too short."""
        with pytest.raises(ValidationError):
            TextProcessingRequest(
                text="Short",  # Less than 10 characters
                operation=ProcessingOperation.SUMMARIZE
            )
    
    def test_text_too_long(self):
        """Test validation fails for text too long."""
        long_text = "A" * 10001  # More than 10000 characters
        with pytest.raises(ValidationError):
            TextProcessingRequest(
                text=long_text,
                operation=ProcessingOperation.SUMMARIZE
            )
    
    def test_invalid_operation(self):
        """Test validation fails for invalid operation."""
        with pytest.raises(ValidationError):
            TextProcessingRequest(
                text="Valid text here",
                operation="invalid_operation"
            )

class TestTextProcessingResponse:
    """Test TextProcessingResponse model."""
    
    def test_basic_response(self):
        """Test basic response creation."""
        response = TextProcessingResponse(
            operation=ProcessingOperation.SUMMARIZE,
            result="This is a summary."
        )
        
        assert response.operation == ProcessingOperation.SUMMARIZE
        assert response.success is True
        assert response.result == "This is a summary."
        assert isinstance(response.timestamp, datetime)
    
    def test_sentiment_response(self):
        """Test sentiment analysis response."""
        sentiment = SentimentResult(
            sentiment="positive",
            confidence=0.9,
            explanation="The text has a positive tone."
        )
        
        response = TextProcessingResponse(
            operation=ProcessingOperation.SENTIMENT,
            sentiment=sentiment
        )
        
        assert response.sentiment.sentiment == "positive"
        assert response.sentiment.confidence == 0.9
    
    def test_key_points_response(self):
        """Test key points response."""
        response = TextProcessingResponse(
            operation=ProcessingOperation.KEY_POINTS,
            key_points=["Point 1", "Point 2", "Point 3"]
        )
        
        assert len(response.key_points) == 3
        assert "Point 1" in response.key_points
    
    def test_questions_response(self):
        """Test questions response."""
        response = TextProcessingResponse(
            operation=ProcessingOperation.QUESTIONS,
            questions=["Question 1?", "Question 2?"]
        )
        
        assert len(response.questions) == 2
        assert all("?" in q for q in response.questions)

class TestSentimentResult:
    """Test SentimentResult model."""
    
    def test_valid_sentiment(self):
        """Test valid sentiment result."""
        sentiment = SentimentResult(
            sentiment="positive",
            confidence=0.85,
            explanation="Text expresses positive emotions."
        )
        
        assert sentiment.sentiment == "positive"
        assert sentiment.confidence == 0.85
    
    def test_confidence_bounds(self):
        """Test confidence score bounds validation."""
        # Test valid bounds
        SentimentResult(sentiment="neutral", confidence=0.0, explanation="Test")
        SentimentResult(sentiment="neutral", confidence=1.0, explanation="Test")
        
        # Test invalid bounds
        with pytest.raises(ValidationError):
            SentimentResult(sentiment="neutral", confidence=-0.1, explanation="Test")
        
        with pytest.raises(ValidationError):
            SentimentResult(sentiment="neutral", confidence=1.1, explanation="Test")

class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_basic_error(self):
        """Test basic error response."""
        error = ErrorResponse(
            error="Something went wrong",
            error_code="PROCESSING_ERROR"
        )
        
        assert error.success is False
        assert error.error == "Something went wrong"
        assert error.error_code == "PROCESSING_ERROR"
        assert isinstance(error.timestamp, datetime)
    
    def test_error_with_details(self):
        """Test error with additional details."""
        error = ErrorResponse(
            error="Validation failed",
            error_code="VALIDATION_ERROR",
            details={"field": "text", "issue": "too short"}
        )
        
        assert error.details["field"] == "text"

class TestHealthResponse:
    """Test HealthResponse model."""
    
    def test_healthy_response(self):
        """Test healthy response."""
        health = HealthResponse(
            ai_model_available=True
        )
        
        assert health.status == "healthy"
        assert health.ai_model_available is True
        assert health.version == "1.0.0"
    
    def test_unhealthy_response(self):
        """Test unhealthy response."""
        health = HealthResponse(
            status="unhealthy",
            ai_model_available=False
        )
        
        assert health.status == "unhealthy"
        assert health.ai_model_available is False

class TestProcessingOperation:
    """Test ProcessingOperation enum."""
    
    def test_all_operations(self):
        """Test all operation values are valid."""
        operations = [
            ProcessingOperation.SUMMARIZE,
            ProcessingOperation.SENTIMENT,
            ProcessingOperation.KEY_POINTS,
            ProcessingOperation.QUESTIONS,
            ProcessingOperation.QA
        ]
        
        assert len(operations) == 5
        assert ProcessingOperation.SUMMARIZE == "summarize"
        assert ProcessingOperation.SENTIMENT == "sentiment"
        assert ProcessingOperation.KEY_POINTS == "key_points"
        assert ProcessingOperation.QUESTIONS == "questions"
        assert ProcessingOperation.QA == "qa"
```

### Create `frontend/tests/` structure:

```
frontend/tests/
├── __init__.py
├── conftest.py
├── test_api_client.py
└── test_config.py
```

### Create `frontend/tests/conftest.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
import httpx

from frontend.app.utils.api_client import APIClient
from shared.models import TextProcessingRequest, TextProcessingResponse, ProcessingOperation

@pytest.fixture
def api_client():
    """Create an API client instance."""
    return APIClient()

@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return "This is a sample text for testing the API client functionality."

@pytest.fixture
def sample_request(sample_text):
    """Sample processing request."""
    return TextProcessingRequest(
        text=sample_text,
        operation=ProcessingOperation.SUMMARIZE,
        options={"max_length": 100}
    )

@pytest.fixture
def sample_response():
    """Sample processing response."""
    return TextProcessingResponse(
        operation=ProcessingOperation.SUMMARIZE,
        success=True,
        result="This is a test summary.",
        processing_time=1.5,
        metadata={"word_count": 50}
    )
```

### Create `frontend/tests/test_api_client.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
import httpx

from frontend.app.utils.api_client import APIClient, run_async
from shared.models import ProcessingOperation

class TestAPIClient:
    """Test the APIClient class."""
    
    async def test_health_check_success(self, api_client):
        """Test successful health check."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.health_check()
            assert result is True
    
    async def test_health_check_failure(self, api_client):
        """Test failed health check."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.health_check()
            assert result is False
    
    async def test_health_check_exception(self, api_client):
        """Test health check with exception."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            
            result = await api_client.health_check()
            assert result is False
    
    async def test_get_operations_success(self, api_client):
        """Test successful get operations."""
        mock_operations = {
            "operations": [
                {
                    "id": "summarize",
                    "name": "Summarize",
                    "description": "Generate summary",
                    "options": ["max_length"]
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_operations
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.get_operations()
            assert result == mock_operations
    
    async def test_get_operations_failure(self, api_client):
        """Test failed get operations."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.get_operations()
            assert result is None
    
    async def test_process_text_success(self, api_client, sample_request, sample_response):
        """Test successful text processing."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_response.dict()
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await api_client.process_text(sample_request)
            assert result is not None
            assert result.operation == ProcessingOperation.SUMMARIZE
            assert result.success is True
    
    async def test_process_text_api_error(self, api_client, sample_request):
        """Test text processing with API error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Bad request"}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with patch('streamlit.error') as mock_error:
                result = await api_client.process_text(sample_request)
                assert result is None
                mock_error.assert_called_once()
    
    async def test_process_text_timeout(self, api_client, sample_request):
        """Test text processing with timeout."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")
            
            with patch('streamlit.error') as mock_error:
                result = await api_client.process_text(sample_request)
                assert result is None
                mock_error.assert_called_once()
    
    async def test_process_text_general_exception(self, api_client, sample_request):
        """Test text processing with general exception."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")
            
            with patch('streamlit.error') as mock_error:
                result = await api_client.process_text(sample_request)
                assert result is None
                mock_error.assert_called_once()

class TestRunAsync:
    """Test the run_async helper function."""
    
    def test_run_async_success(self):
        """Test successful async execution."""
        async def test_coro():
            return "success"
        
        result = run_async(test_coro())
        assert result == "success"
    
    def test_run_async_with_exception(self):
        """Test async execution with exception."""
        async def test_coro():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            run_async(test_coro())
```

### Create `frontend/tests/test_config.py`:

```python
import pytest
from unittest.mock import patch
import os

from frontend.app.config import Settings, settings

class TestSettings:
    """Test the Settings configuration class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            
            assert test_settings.api_base_url == "http://backend:8000"
            assert test_settings.page_title == "AI Text Processor"
            assert test_settings.page_icon == "🤖"
            assert test_settings.layout == "wide"
            assert test_settings.show_debug_info is False
            assert test_settings.max_text_length == 10000
    
    def test_environment_override(self):
        """Test environment variable overrides."""
        env_vars = {
            "API_BASE_URL": "http://localhost:8000",
            "SHOW_DEBUG_INFO": "true",
            "MAX_TEXT_LENGTH": "5000"
        }
        
        with patch.dict(os.environ, env_vars):
            test_settings = Settings()
            
            assert test_settings.api_base_url == "http://localhost:8000"
            assert test_settings.show_debug_info is True
            assert test_settings.max_text_length == 5000
    
    def test_global_settings_instance(self):
        """Test global settings instance."""
        assert settings is not None
        assert isinstance(settings, Settings)
```

### Create test runner script `run_tests.py`:

```python
#!/usr/bin/env python3
"""
Test runner script for the FastAPI-Streamlit-LLM starter template.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    """Main test runner."""
    print("FastAPI-Streamlit-LLM Starter Template Test Runner")
    print("=" * 60)
    
    # Get project root
    project_root = Path(__file__).parent
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    
    # Check if we're running in Docker or locally
    in_docker = os.environ.get('DOCKER_ENVIRONMENT', False)
    
    success_count = 0
    total_tests = 0
    
    # Backend tests
    if backend_dir.exists():
        print(f"\n🔧 Testing Backend ({backend_dir})")
        os.chdir(backend_dir)
        
        # Install dependencies
        if not in_docker:
            success = run_command(
                ["pip", "install", "-r", "requirements.txt"],
                "Installing backend dependencies"
            )
            if not success:
                print("❌ Failed to install backend dependencies")
                return 1
        
        # Run pytest with coverage
        test_commands = [
            (["python", "-m", "pytest", "tests/", "-v"], "Running backend unit tests"),
            (["python", "-m", "pytest", "tests/", "--cov=app", "--cov-report=html"], "Running backend tests with coverage"),
            (["python", "-m", "flake8", "app/"], "Running code style checks"),
            (["python", "-m", "mypy", "app/"], "Running type checking")
        ]
        
        for command, description in test_commands:
            total_tests += 1
            if run_command(command, description):
                success_count += 1
    
    # Frontend tests
    if frontend_dir.exists():
        print(f"\n🎨 Testing Frontend ({frontend_dir})")
        os.chdir(frontend_dir)
        
        # Install dependencies
        if not in_docker:
            success = run_command(
                ["pip", "install", "-r", "requirements.txt"],
                "Installing frontend dependencies"
            )
            if not success:
                print("❌ Failed to install frontend dependencies")
                return 1
        
        # Run pytest
        test_commands = [
            (["python", "-m", "pytest", "tests/", "-v"], "Running frontend unit tests"),
            (["python", "-m", "pytest", "tests/", "--cov=app"], "Running frontend tests with coverage"),
        ]
        
        for command, description in test_commands:
            total_tests += 1
            if run_command(command, description):
                success_count += 1
    
    # Integration tests (if Docker is available)
    os.chdir(project_root)
    if Path("docker-compose.yml").exists():
        print(f"\n🐳 Running Integration Tests")
        
        integration_commands = [
            (["docker-compose", "build"], "Building Docker images"),
            (["docker-compose", "up", "-d"], "Starting services"),
            (["sleep", "30"], "Waiting for services to start"),
            (["curl", "-f", "http://localhost:8000/health"], "Testing backend health"),
            (["curl", "-f", "http://localhost:8501/_stcore/health"], "Testing frontend health"),
            (["docker-compose", "down"], "Stopping services")
        ]
        
        for command, description in integration_commands:
            total_tests += 1
            if run_command(command, description):
                success_count += 1
    
    # Results summary
    print(f"\n{'='*60}")
    print(f"TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {success_count}/{total_tests}")
    print(f"❌ Failed: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"💥 {total_tests - success_count} test(s) failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Add to requirements files for testing:

**`backend/requirements-dev.txt`:**
```txt
# Testing dependencies
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
httpx==0.25.0

# Code quality
flake8==6.0.0
mypy==1.5.0
black==23.7.0
isort==5.12.0

# Development tools
pre-commit==3.3.0
```

**`frontend/requirements-dev.txt`:**
```txt
# Testing dependencies
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0

# Code quality
flake8==6.0.0
black==23.7.0
isort==5.12.0
```

### Create `.github/workflows/ci.yml` for GitHub Actions:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: |
        cd backend
        python -m pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend

  test-frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd frontend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        cd frontend
        python -m pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage.xml
        flags: frontend

  integration-tests:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and test with Docker Compose
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: |
        docker-compose build
        docker-compose up -d
        sleep 30
        
        # Test backend health
        curl -f http://localhost:8000/health
        
        # Test frontend health  
        curl -f http://localhost:8501/_stcore/health
        
        # Test API functionality
        curl -X POST http://localhost:8000/process \
          -H "Content-Type: application/json" \
          -d '{"text":"Test text for processing","operation":"summarize"}'
        
        docker-compose down

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security scan
      uses: securecodewarrior/github-action-add-sarif@v1
      with:
        sarif-file: 'security-scan-results.sarif'
    
    - name: Scan Python dependencies
      run: |
        pip install safety
        safety check --json --output safety-report.json || true
```

### Key Testing Features:
- Comprehensive unit tests for backend and frontend
- Integration tests with Docker
- Code coverage reporting
- Type checking and code quality checks
- CI/CD pipeline with GitHub Actions
- Security scanning for dependencies
- Easy test runner script for local development
- Mock data for testing without API calls

---

## Prompt 7: Final Integration & Summary

**Objective:** Create the final integration prompt that ties everything together and provides usage examples.

### Create comprehensive usage examples in `examples/` directory:

**`examples/basic_usage.py`:**
```python
#!/usr/bin/env python3
"""
Basic usage examples for the FastAPI-Streamlit-LLM Starter Template.
"""

import asyncio
import httpx
from shared.models import TextProcessingRequest, ProcessingOperation

async def main():
    """Demonstrate basic API usage."""
    
    # Sample text for processing
    sample_text = """
    Climate change represents one of the most significant challenges facing humanity today. 
    Rising global temperatures, caused primarily by increased greenhouse gas emissions, 
    are leading to more frequent extreme weather events, rising sea levels, and 
    disruptions to ecosystems worldwide. Scientists agree that immediate action is 
    required to mitigate these effects and transition to sustainable energy sources.
    """
    
    # API base URL
    api_url = "http://localhost:8000"
    
    print("🤖 FastAPI-Streamlit-LLM Starter Template Examples")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        
        # 1. Health Check
        print("\n1️⃣ Health Check")
        health_response = await client.get(f"{api_url}/health")
        print(f"Status: {health_response.status_code}")
        print(f"Response: {health_response.json()}")
        
        # 2. Get Available Operations
        print("\n2️⃣ Available Operations")
        ops_response = await client.get(f"{api_url}/operations")
        operations = ops_response.json()
        print("Available operations:")
        for op in operations["operations"]:
            print(f"  • {op['name']}: {op['description']}")
        
        # 3. Text Summarization
        print("\n3️⃣ Text Summarization")
        summarize_request = {
            "text": sample_text,
            "operation": "summarize",
            "options": {"max_length": 50}
        }
        response = await client.post(f"{api_url}/process", json=summarize_request)
        result = response.json()
        print(f"Summary: {result['result']}")
        print(f"Processing time: {result['processing_time']:.2f}s")
        
        # 4. Sentiment Analysis
        print("\n4️⃣ Sentiment Analysis")
        sentiment_request = {
            "text": sample_text,
            "operation": "sentiment"
        }
        response = await client.post(f"{api_url}/process", json=sentiment_request)
        result = response.json()
        sentiment = result['sentiment']
        print(f"Sentiment: {sentiment['sentiment']}")
        print(f"Confidence: {sentiment['confidence']:.2%}")
        print(f"Explanation: {sentiment['explanation']}")
        
        # 5. Key Points Extraction
        print("\n5️⃣ Key Points Extraction")
        keypoints_request = {
            "text": sample_text,
            "operation": "key_points",
            "options": {"max_points": 3}
        }
        response = await client.post(f"{api_url}/process", json=keypoints_request)
        result = response.json()
        print("Key points:")
        for i, point in enumerate(result['key_points'], 1):
            print(f"  {i}. {point}")
        
        # 6. Question Generation
        print("\n6️⃣ Question Generation")
        questions_request = {
            "text": sample_text,
            "operation": "questions",
            "options": {"num_questions": 3}
        }
        response = await client.post(f"{api_url}/process", json=questions_request)
        result = response.json()
        print("Generated questions:")
        for i, question in enumerate(result['questions'], 1):
            print(f"  {i}. {question}")
        
        # 7. Question & Answer
        print("\n7️⃣ Question & Answer")
        qa_request = {
            "text": sample_text,
            "operation": "qa",
            "question": "What is the main cause of climate change mentioned in the text?"
        }
        response = await client.post(f"{api_url}/process", json=qa_request)
        result = response.json()
        print(f"Question: {qa_request['question']}")
        print(f"Answer: {result['result']}")

if __name__ == "__main__":
    asyncio.run(main())
```

**`examples/custom_operation.py`:**
```python
#!/usr/bin/env python3
"""
Example of how to add a custom text processing operation.
"""

# Step 1: Add new operation to shared models
from enum import Enum
from shared.models import ProcessingOperation

# Extend the enum (in shared/models.py)
class ExtendedProcessingOperation(str, Enum):
    SUMMARIZE = "summarize"
    SENTIMENT = "sentiment"
    KEY_POINTS = "key_points"
    QUESTIONS = "questions"
    QA = "qa"
    TRANSLATE = "translate"  # New operation
    CLASSIFY = "classify"    # Another new operation

# Step 2: Add backend logic (in backend/app/services/text_processor.py)
async def _translate_text(self, text: str, options: Dict[str, Any]) -> str:
    """Translate text to target language."""
    target_language = options.get("target_language", "Spanish")
    
    prompt = f"""
    Translate the following text to {target_language}:
    
    Text: {text}
    
    Translation:
    """
    
    result = await self.agent.run(prompt)
    return result.data.strip()

async def _classify_text(self, text: str, options: Dict[str, Any]) -> str:
    """Classify text into categories."""
    categories = options.get("categories", ["News", "Opinion", "Technical", "Educational"])
    
    prompt = f"""
    Classify the following text into one of these categories: {', '.join(categories)}
    
    Text: {text}
    
    Category:
    """
    
    result = await self.agent.run(prompt)
    return result.data.strip()

# Step 3: Update main processing method
async def process_text(self, request: TextProcessingRequest) -> TextProcessingResponse:
    """Process text with extended operations."""
    # ... existing code ...
    
    elif request.operation == ProcessingOperation.TRANSLATE:
        result = await self._translate_text(request.text, request.options)
    elif request.operation == ProcessingOperation.CLASSIFY:
        result = await self._classify_text(request.text, request.options)
    
    # ... rest of existing code ...

# Step 4: Update frontend UI (in frontend/app/app.py)
def create_sidebar():
    """Enhanced sidebar with new operations."""
    # ... existing code ...
    
    if "target_language" in op_info.get("options", []):
        options["target_language"] = st.selectbox(
            "Target Language",
            ["Spanish", "French", "German", "Italian", "Portuguese"],
            key="target_language"
        )
    
    if "categories" in op_info.get("options", []):
        default_categories = ["News", "Opinion", "Technical", "Educational"]
        categories = st.multiselect(
            "Classification Categories",
            default_categories,
            default=default_categories,
            key="categories"
        )
        if categories:
            options["categories"] = categories

# Step 5: Update operations endpoint (in backend/app/main.py)
@app.get("/operations")
async def get_operations():
    """Enhanced operations list."""
    return {
        "operations": [
            # ... existing operations ...
            {
                "id": "translate",
                "name": "Translate",
                "description": "Translate text to another language",
                "options": ["target_language"]
            },
            {
                "id": "classify",
                "name": "Classify",
                "description": "Classify text into categories",
                "options": ["categories"]
            }
        ]
    }

print("✨ Custom operations added successfully!")
print("Remember to update all relevant files:")
print("1. shared/models.py - Add new enum values")
print("2. backend/app/services/text_processor.py - Add processing methods")
print("3. backend/app/main.py - Update operations endpoint")
print("4. frontend/app/app.py - Add UI controls")
print("5. Run tests to ensure everything works!")
```
