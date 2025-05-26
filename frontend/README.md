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