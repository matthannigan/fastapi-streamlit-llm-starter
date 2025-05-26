#!/bin/bash

# Docker Setup Script for FastAPI Streamlit LLM Starter
# This script helps set up the Docker environment

set -e

echo "🐳 FastAPI Streamlit LLM Starter - Docker Setup"
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cat > .env << EOF
# API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.7

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
SHOW_DEBUG_INFO=false
MAX_TEXT_LENGTH=10000

# Redis Configuration
REDIS_URL=redis://redis:6379

# Network Configuration
ALLOWED_ORIGINS=["http://localhost:8501", "http://frontend:8501"]

# Development/Production Toggle
ENVIRONMENT=development
EOF
    echo "📝 Created .env file. Please update GEMINI_API_KEY with your actual API key."
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backups
mkdir -p nginx/ssl
echo "✅ Directories created"

# Build Docker images
echo "🏗️  Building Docker images..."
docker-compose build

echo ""
echo "🎉 Docker setup complete!"
echo ""
echo "Next steps:"
echo "1. Update your GEMINI_API_KEY in the .env file"
echo "2. Start development environment: make dev"
echo "3. Or start production environment: make prod"
echo ""
echo "Available commands:"
echo "  make help    - Show all available commands"
echo "  make dev     - Start development environment"
echo "  make prod    - Start production environment"
echo "  make status  - Check service status"
echo "  make logs    - View logs"
echo "  make clean   - Clean up Docker resources"
echo ""
echo "For more information, see DOCKER_README.md" 