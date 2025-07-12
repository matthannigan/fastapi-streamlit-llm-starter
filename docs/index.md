# AI Text Processor API Documentation

Welcome to the AI Text Processor API documentation. This FastAPI application provides text processing capabilities using various AI models.

## Features

- **Text Processing**: Summarize, analyze, and answer questions about text
- **Batch Processing**: Process multiple texts in batches
- **Authentication**: Secure API key-based authentication
- **Caching**: Intelligent response caching for improved performance
- **Monitoring**: Health checks and performance monitoring
- **Resilience**: Circuit breakers and retry mechanisms

## Quick Start

1. **Authentication**: Obtain an API key and include it in your requests
2. **Process Text**: Use the `/process` endpoint to analyze text
3. **Batch Operations**: Use `/batch_process` for multiple texts
4. **Monitor**: Check `/health` for system status

## API Endpoints

### Core Endpoints
- `POST /process` - Process a single text
- `POST /batch_process` - Process multiple texts
- `GET /operations` - List available operations
- `GET /health` - Health check

### Cache Management
- `GET /cache/status` - Cache statistics
- `POST /cache/invalidate` - Clear cache entries
- `GET /cache/invalidation-stats` - Invalidation statistics

### Authentication
- `GET /auth/status` - Check authentication status

## Available Operations

- **summarize**: Generate concise summaries
- **analyze**: Analyze text content and structure
- **qa**: Answer questions about text content

For detailed API reference, see the [Backend API Reference]() and [Shared Models]() sections. 