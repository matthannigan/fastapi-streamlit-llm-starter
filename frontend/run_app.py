#!/usr/bin/env python3
"""Launcher script for the Streamlit app with proper Python path setup."""

import sys
import os

# Add the current directory to Python path to ensure app package is found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Debug information
print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path}")
print(f"Contents of current directory: {os.listdir(current_dir)}")

# Verify app package is available
try:
    import app
    print(f"App package found at: {app.__file__}")
except ImportError as e:
    print(f"Failed to import app package: {e}")
    print("This might indicate a path issue")

# Run the Streamlit app
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    # Set up Streamlit arguments
    sys.argv = [
        "streamlit",
        "run",
        "app/app.py",
        "--server.address=0.0.0.0",
        "--server.port=8501"
    ]
    
    # Add runOnSave for development
    if os.getenv("STREAMLIT_ENV") == "development":
        sys.argv.append("--server.runOnSave=true")
    
    stcli.main() 