# Shared Module

This package contains shared Python code for the project, including:

## Features

- **Models**: Pydantic models for data validation and serialization
- **Sample Data**: Standardized sample data for consistent examples across the codebase
- **Examples**: Demonstration code showing how to use the various models

## Installation

This package is designed to be installed in editable mode from the project's backend and frontend environments:

```bash
pip install -e ../shared
```

## Usage

```python
from shared.models import TextProcessingRequest, ProcessingOperation
from shared.sample_data import get_sample_text

# Create a processing request
request = TextProcessingRequest(
    text=get_sample_text("ai_technology"),
    operation=ProcessingOperation.SUMMARIZE
)
```

## Dependencies

- Python >=3.8
- Pydantic >=2.0

## Development

To install development dependencies:

```bash
pip install -e ".[dev]"
``` 