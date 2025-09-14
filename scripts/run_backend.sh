#!/bin/bash

# FastAPI Backend Development Server
# This script follows the same patterns as the Makefile for consistency

set -e  # Exit on error

echo "🚀 Starting FastAPI Backend Development Server..."

# Python executable detection (same as Makefile)
PYTHON=$(command -v python3 2> /dev/null || command -v python 2> /dev/null)
if [ -z "$PYTHON" ]; then
    echo "❌ Error: Python not found. Please install Python 3.7+"
    exit 1
fi

# Check if Poetry is available and backend has Poetry configuration
if command -v poetry >/dev/null 2>&1 && [ -f "backend/pyproject.toml" ]; then
    echo "✅ Using Poetry for backend environment..."
    PYTHON_CMD="poetry run python"
    # Ensure Poetry virtual environment is set up
    cd backend && poetry install --with dev,test --quiet && cd ..
else
    echo "📦 Creating virtual environment at $VENV_DIR..."
    $PYTHON -m venv "$VENV_DIR"
    echo "⬆️  Upgrading pip..."
    "$VENV_PIP" install --upgrade pip
    echo "🔧 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    PYTHON_CMD="$VENV_PYTHON"
    PIP_CMD="$VENV_PIP"
fi

# Navigate to backend directory
cd backend

# Install dependencies using lock files (consistent with Makefile)
echo "📥 Installing backend dependencies from lock files..."
if [ -f "requirements.lock" ] && [ -f "requirements-dev.lock" ]; then
    $PIP_CMD install -r requirements.lock -r requirements-dev.lock
elif [ -f "requirements.txt" ]; then
    echo "⚠️  Warning: Using requirements.txt (lock files not found)"
    echo "   Consider running 'make lock-deps' to generate lock files"
    $PIP_CMD install -r requirements.txt
    if [ -f "requirements-dev.txt" ]; then
        $PIP_CMD install -r requirements-dev.txt
    fi
else
    echo "❌ Error: No requirements files found"
    exit 1
fi

# Environment setup
echo "🔧 Setting up environment..."
if [ -f "../.env" ]; then
    echo "✅ Found .env file"
    # Note: uvicorn will automatically load .env file from project root
else
    echo "⚠️  Warning: No .env file found. Create one from .env.example if needed"
fi

# Health check
echo "🔍 Checking Python installation..."
$PYTHON_CMD --version

# Start the server with proper configuration
echo ""
echo "🌟 Starting FastAPI server..."
echo "   📍 Backend URL: http://localhost:8000"
echo "   📚 API Docs: http://localhost:8000/docs"
echo "   🔧 Admin Panel: http://localhost:8000/admin (if enabled)"
echo ""
echo "💡 Tips:"
echo "   • Press Ctrl+C to stop the server"
echo "   • Server will auto-reload on code changes"
echo "   • Use 'make test-backend' to run tests"
echo "   • Use 'make lint-backend' for code quality checks"
echo ""

# Run the server with proper host binding and reload
if [[ "$PYTHON_CMD" == "poetry run python" ]]; then
    # Poetry command needs to run from backend directory
    exec sh -c "cd backend && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app --log-level info"
else
    # Traditional virtual environment
    exec $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app --log-level info
fi 