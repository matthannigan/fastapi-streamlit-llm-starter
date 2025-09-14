# Shared Module

**Common data models and utilities for the FastAPI + Streamlit LLM Starter Template**

This package provides shared Pydantic models, sample data, and utilities used across both the FastAPI backend and Streamlit frontend components of the starter template. It ensures type safety, data consistency, and standardized examples throughout the application.

## Installation

Install the shared module using Poetry:

```bash
poetry add --path ../shared
```

## Available Models

- **`TextProcessingOperation`**: AI operations enumeration
- **`TextProcessingRequest`**: Input validation for single text processing
- **`TextProcessingResponse`**: Comprehensive response structure
- **`SentimentResult`**: Structured sentiment analysis results
- **Batch Processing Models**: Support for batch text processing operations

For complete documentation, see the main project documentation.