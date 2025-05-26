#!/bin/bash

# Streamlit Frontend Development Server
echo "🎨 Starting Streamlit Frontend..."

# Navigate to frontend directory
cd frontend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Run the server
echo "🌟 Starting server on http://localhost:8501"
streamlit run app/app.py --server.port 8501 --server.address 0.0.0.0 