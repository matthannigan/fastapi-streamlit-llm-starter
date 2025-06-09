# Base stage
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared directory first for shared library installation
COPY shared/ ./shared/

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt backend/requirements.docker.txt ./
RUN pip install --no-cache-dir -r requirements.docker.txt

# Add shared models to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Development stage
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir \
    black \
    isort \
    flake8 \
    mypy \
    pytest \
    pytest-asyncio

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
FROM base AS production

# Copy lock files
COPY backend/requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

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