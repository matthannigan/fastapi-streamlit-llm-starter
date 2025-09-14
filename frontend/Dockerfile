# Base stage
FROM python:3.13-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared directory first for shared library installation
COPY shared/ ./shared/

# Copy frontend requirements and install Python dependencies
COPY frontend/requirements.txt frontend/requirements.docker.txt ./
RUN pip install --no-cache-dir -r requirements.docker.txt

# Add shared models to Python path - app package is already available from /app
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Development stage
FROM base AS development

# Copy and install development dependencies
COPY frontend/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

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

# Copy lock files
COPY frontend/requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

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