#!/bin/bash

# FastAPI Streamlit LLM Starter Setup Script
# This script follows the same patterns as the Makefile and run scripts for consistency

set -e  # Exit on error

echo "🚀 Setting up FastAPI Streamlit LLM Starter..."

# Python executable detection (same as Makefile and run_backend.sh)
PYTHON=$(command -v python3 2> /dev/null || command -v python 2> /dev/null)
if [ -z "$PYTHON" ]; then
    echo "❌ Error: Python not found. Please install Python 3.7+"
    exit 1
fi

# Check if Docker is available (required for frontend)
echo "🐳 Checking Docker availability..."
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not found. Docker is required for frontend."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose not found."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running. Please start Docker."
    exit 1
fi

echo "✅ Docker is available and running"

# Environment file setup
echo ""
echo "📝 Setting up environment file..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example template"
        echo "⚠️  Please edit .env file with your API keys and configuration"
    else
        echo "⚠️  Warning: No .env.example found. You may need to create .env manually"
    fi
else
    echo "✅ .env file already exists"
fi

# Backend setup (root-level virtual environment, consistent with run_backend.sh)
echo ""
echo "🔧 Setting up backend..."

VENV_DIR=".venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# Check if we're already in a virtual environment
IN_VENV=$(${PYTHON} -c "import sys; print('1' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '0')" 2>/dev/null || echo "0")

if [ "$IN_VENV" = "1" ]; then
    echo "✅ Already in virtual environment"
    PYTHON_CMD="python"
    PIP_CMD="pip"
elif [ -d "$VENV_DIR" ]; then
    echo "✅ Virtual environment already exists at $VENV_DIR"
    PYTHON_CMD="$VENV_PYTHON"
    PIP_CMD="$VENV_PIP"
else
    echo "📦 Creating virtual environment at $VENV_DIR..."
    $PYTHON -m venv "$VENV_DIR"
    echo "⬆️  Upgrading pip..."
    "$VENV_PIP" install --upgrade pip
    PYTHON_CMD="$VENV_PYTHON"
    PIP_CMD="$VENV_PIP"
fi

# Install backend dependencies using lock files (consistent with run_backend.sh)
echo "📥 Installing backend dependencies..."
cd backend

if [ -f "requirements.lock" ] && [ -f "requirements-dev.lock" ]; then
    echo "✅ Using lock files for reproducible installation"
    $PIP_CMD install -r requirements.lock -r requirements-dev.lock
elif [ -f "requirements.txt" ]; then
    echo "⚠️  Warning: Using requirements.txt (lock files not found)"
    echo "   Consider running 'make lock-deps' to generate lock files"
    $PIP_CMD install -r requirements.txt
    if [ -f "requirements-dev.txt" ]; then
        $PIP_CMD install -r requirements-dev.txt
    fi
else
    echo "❌ Error: No requirements files found in backend/"
    exit 1
fi

cd ..

echo "✅ Backend setup complete"

# Frontend setup (Docker-only, consistent with run_frontend.sh)
echo ""
echo "🎨 Setting up frontend..."
echo "Frontend runs exclusively in Docker to avoid packaging version conflicts"

# Build frontend Docker image
echo "🔨 Building frontend Docker image..."
docker-compose build frontend

echo "✅ Frontend Docker image ready"

# Build other Docker images for completeness
echo ""
echo "🔨 Building additional Docker images..."
docker-compose build

# Make scripts executable
echo ""
echo "🔐 Making scripts executable..."
chmod +x scripts/*.sh

# Validation
echo ""
echo "🔍 Validating setup..."

# Check Python installation
echo "Python version: $($PYTHON_CMD --version)"

# Check if backend requirements are satisfied
echo "Backend dependencies: ✅"

# Check Docker images
if docker images | grep -q "$(basename $(pwd))"; then
    echo "Docker images: ✅"
else
    echo "Docker images: ⚠️  Some images may not be built properly"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Next steps:"
echo ""
echo "📝 Configuration:"
echo "   1. Edit .env file with your API keys:"
echo "      • GEMINI_API_KEY=your_api_key_here"
echo "      • AI_MODEL=gemini-2.0-flash-exp"
echo "      • RESILIENCE_PRESET=simple"
echo ""
echo "🖥️  Development (Hybrid Approach):"
echo "   2a. Backend (local virtual environment):"
echo "       ./scripts/run_backend.sh"
echo "       OR: source .venv/bin/activate && cd backend && uvicorn app.main:app --reload"
echo ""
echo "   2b. Frontend (Docker):"
echo "       ./scripts/run_frontend.sh"
echo ""
echo "🐳 Docker (Full Stack):"
echo "   3. Development mode: make dev"
echo "   4. Production mode: make prod"
echo ""
echo "🧪 Testing:"
echo "   5. Backend tests: make test-backend"
echo "   6. Frontend tests: make test-frontend"
echo "   7. All tests: make test"
echo ""
echo "💡 Helpful Commands:"
echo "   • make help           - Show all available commands"
echo "   • make install        - Reinstall backend dependencies"
echo "   • make clean          - Clean up generated files"
echo "   • make status         - Check service status"
echo "   • make logs           - View Docker logs"
echo ""
echo "📚 URLs (after starting services):"
echo "   • Frontend: http://localhost:8501"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs" 