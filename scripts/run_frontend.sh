#!/bin/bash

# Streamlit Frontend Development Server
# Frontend runs exclusively in Docker to avoid packaging version conflicts

set -e  # Exit on error

echo "🎨 Starting Streamlit Frontend Development Server..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not found. Please install Docker to run the frontend."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose not found. Please install Docker Compose."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running. Please start Docker."
    exit 1
fi

# Environment setup check
echo "🔧 Checking environment setup..."
if [ -f ".env" ]; then
    echo "✅ Found .env file"
else
    echo "⚠️  Warning: No .env file found. Create one from .env.example if needed"
    echo "   Some features may not work without proper environment variables"
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Make sure you're in the project root."
    exit 1
fi

# Build frontend image if it doesn't exist or if forced
echo "🔨 Building frontend Docker image (if needed)..."
docker-compose build frontend

# Check if backend is running (frontend depends on it)
echo "🔍 Checking backend availability..."
if curl -f http://localhost:8000/health &>/dev/null; then
    echo "✅ Backend is running at http://localhost:8000"
else
    echo "⚠️  Warning: Backend not detected at http://localhost:8000"
    echo "   Frontend will still start but API features may not work"
    echo "   To start backend: ./scripts/run_backend.sh or cd backend && poetry run uvicorn app.main:app --reload"
fi

# Start dependencies (Redis) if not already running
echo "🚀 Starting dependencies..."
docker-compose up -d redis

# Start the frontend server with proper configuration
echo ""
echo "🌟 Starting Streamlit frontend via Docker..."
echo "   📍 Frontend URL: http://localhost:8501"
echo "   🔧 Streamlit Admin: http://localhost:8501/_stcore/health"
echo ""
echo "💡 Tips:"
echo "   • Press Ctrl+C to stop the server"
echo "   • Frontend auto-reloads on code changes (via volume mounts)"
echo "   • Use 'make test-frontend' to run frontend tests"
echo "   • Use 'make lint-frontend' for code quality checks"
echo "   • Logs available with: docker-compose logs -f frontend"
echo ""
echo "🐳 Docker Info:"
echo "   • Frontend runs in isolated Docker environment"
echo "   • No local virtual environment needed"
echo "   • Dependencies managed via Docker image"
echo ""

# Run the frontend service with proper cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down frontend..."
    docker-compose stop frontend
    exit 0
}

# Set up cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start frontend in foreground with logs
exec docker-compose up frontend 