# AI Text Processing Frontend Application.

This module provides a Streamlit-based web interface for an AI text processing service.
It demonstrates best practices for building interactive data applications that connect
to backend APIs, handle user input validation, and provide real-time feedback.

The application supports multiple text processing operations including:
- Text summarization with configurable length
- Sentiment analysis with confidence scoring
- Key point extraction with customizable count
- Question generation for educational purposes
- Question & Answer functionality

## Key Features

- Real-time API health monitoring
- Operation-specific parameter configuration
- Example text library with categorized samples
- File upload support for text documents
- Results caching and download functionality
- Responsive UI with progress indicators
- Error handling and user feedback

## Architecture

The application follows a modular design pattern with clear separation of concerns:
- UI rendering functions for each component
- API communication through a dedicated client
- Centralized configuration management
- Standardized sample data from shared module

## Example

Run the application with:
streamlit run app.py

### Or via Docker

docker-compose up frontend

## Dependencies

- streamlit: Web application framework
- shared: Custom module containing data models and sample texts
- utils.api_client: Backend API communication layer
- config: Application configuration settings

Author: AI Text Processing Team
Version: 1.0.0
