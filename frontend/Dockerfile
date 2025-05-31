# Base stage
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared directory first for shared library installation
COPY shared/ ./shared/

# Copy frontend requirements and install Python dependencies
COPY frontend/requirements.txt frontend/requirements.docker.txt ./
RUN pip install --no-cache-dir -r requirements.docker.txt

# Add shared models to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Development stage
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio

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

# Run the application with hot reload
CMD ["streamlit", "run", "app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.runOnSave", "true"]

# Production stage
FROM base AS production

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

# Run the application
CMD ["streamlit", "run", "app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

# Default to production 