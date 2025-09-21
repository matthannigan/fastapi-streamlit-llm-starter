# Dependency stage
FROM python:3.13-slim AS dependencies

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared directory first for shared library installation
COPY shared/ ./shared/

# Copy requirements for Docker build
COPY backend/requirements.docker.txt ./

# Install dependencies using pip (simpler than Poetry for Docker)
RUN pip install --no-cache-dir -r requirements.docker.txt

# Base stage
FROM dependencies AS base

# Add shared models to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Development stage
FROM base AS development

# Install development dependencies
RUN if [ -f "pyproject.toml" ]; then \
        poetry install --with dev && rm -rf $POETRY_CACHE_DIR; \
    else \
        pip install --no-cache-dir \
            black \
            isort \
            flake8 \
            mypy \
            pytest \
            pytest-asyncio; \
    fi

# Copy backend application code (excluding local shared directory)
COPY backend/app/ ./app/
COPY backend/tests/ ./tests/
COPY backend/*.py ./
COPY backend/*.ini ./
COPY backend/*.txt ./

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM python:3.13-slim AS production

WORKDIR /app

# Install system dependencies (minimal for production)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared directory
COPY shared/ ./shared/

# Install production dependencies
COPY backend/requirements.docker.txt ./

RUN pip install --no-cache-dir -r requirements.docker.txt

# Copy backend application code (excluding local shared directory)
COPY backend/app/ ./app/
COPY backend/tests/ ./tests/
COPY backend/*.py ./
COPY backend/*.ini ./
COPY backend/*.txt ./

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Default to production 