# Poetry installation stage
FROM python:3.13-slim AS poetry-base

# Install Poetry
RUN pip install poetry==2.1.4

# Configure Poetry for Docker
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Dependency stage
FROM poetry-base AS dependencies

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared directory first for shared library installation
COPY shared/ ./shared/

# Choose installation method based on available files
COPY backend/pyproject.toml* backend/poetry.lock* backend/requirements.txt* backend/requirements.docker.txt* ./

# Install dependencies with Poetry if pyproject.toml exists, otherwise use pip
RUN if [ -f "pyproject.toml" ]; then \
        cd ../shared && poetry install && cd /app; \
        poetry install --only=main && rm -rf $POETRY_CACHE_DIR; \
    else \
        pip install --no-cache-dir -r requirements.docker.txt; \
    fi

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

# Production export stage (for Poetry optimization)
FROM poetry-base AS production-export

WORKDIR /app

# Copy shared and backend Poetry files
COPY shared/ ./shared/
COPY backend/pyproject.toml* backend/poetry.lock* ./

# Export requirements.txt for production build
RUN if [ -f "pyproject.toml" ]; then \
        cd ../shared && poetry install && cd /app; \
        poetry export -f requirements.txt --output requirements-prod.txt --without-hashes; \
    fi

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
COPY backend/requirements.lock* ./
COPY --from=production-export /app/requirements-prod.txt* ./

RUN if [ -f "requirements-prod.txt" ]; then \
        pip install --no-cache-dir -r requirements-prod.txt; \
    else \
        pip install --no-cache-dir -r requirements.lock; \
    fi

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