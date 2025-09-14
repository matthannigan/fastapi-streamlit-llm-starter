# Base stage
FROM python:3.13-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==2.1.4

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy shared directory first for shared library installation
COPY shared/ ./shared/

# Choose installation method based on available files
COPY frontend/pyproject.toml* frontend/poetry.lock* frontend/requirements.txt* frontend/requirements.docker.txt* ./

# Install dependencies with Poetry if pyproject.toml exists, otherwise use pip
RUN if [ -f "pyproject.toml" ]; then \
        cd ../shared && poetry install && cd /app; \
        poetry install --only=main && rm -rf $POETRY_CACHE_DIR; \
    else \
        pip install --no-cache-dir -r requirements.docker.txt; \
    fi

# Add shared models to Python path - app package is already available from /app
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Development stage
FROM base AS development

# Install development dependencies
RUN if [ -f "pyproject.toml" ]; then \
        poetry install --with dev && rm -rf $POETRY_CACHE_DIR; \
    else \
        pip install --no-cache-dir -r requirements-dev.txt; \
    fi

# Copy frontend application code (excluding local shared directory)
COPY frontend/app/ ./app/
COPY frontend/tests/ ./tests/
COPY frontend/*.py ./
COPY frontend/*.ini ./
COPY frontend/*.txt ./

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health

# Set environment for development
ENV STREAMLIT_ENV=development

# Run the application with hot reload using launcher script
CMD ["python", "run_app.py"]

# Production stage
FROM base AS production

# Install production dependencies
RUN if [ -f "pyproject.toml" ]; then \
        poetry install --only=main && rm -rf $POETRY_CACHE_DIR; \
    else \
        pip install --no-cache-dir -r requirements.lock; \
    fi

# Copy frontend application code (excluding local shared directory)
COPY frontend/app/ ./app/
COPY frontend/tests/ ./tests/
COPY frontend/*.py ./
COPY frontend/*.ini ./
COPY frontend/*.txt ./

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health

# Run the application using launcher script
CMD ["python", "run_app.py"]

# Default to production 