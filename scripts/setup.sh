#!/bin/bash

# FastAPI Streamlit LLM Starter Setup Script
echo "🚀 Setting up FastAPI Streamlit LLM Starter..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
else
    echo "✅ .env file already exists"
fi

# Setup backend
echo "🔧 Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "📦 Creating backend virtual environment..."
    python -m venv venv
fi
source venv/bin/activate
echo "📥 Installing backend dependencies..."
pip install -r requirements.txt
deactivate
cd ..

# Setup frontend
echo "🎨 Setting up frontend..."
cd frontend
if [ ! -d "venv" ]; then
    echo "📦 Creating frontend virtual environment..."
    python -m venv venv
fi
source venv/bin/activate
echo "📥 Installing frontend dependencies..."
pip install -r requirements.txt
deactivate
cd ..

# Make scripts executable
echo "🔐 Making scripts executable..."
chmod +x scripts/*.sh

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run backend: ./scripts/run_backend.sh"
echo "3. Run frontend: ./scripts/run_frontend.sh"
echo "4. Or use Docker: docker-compose up" 