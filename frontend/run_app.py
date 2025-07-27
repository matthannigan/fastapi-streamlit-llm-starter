#!/usr/bin/env python3
"""Launcher script for the Streamlit frontend with Python path configuration and debugging.

This module serves as the entry point for running the Streamlit frontend application with proper
Python path setup and import resolution. It handles environment-specific configuration and
provides comprehensive debugging output for troubleshooting deployment issues.

The script automatically configures the Python path to ensure all application modules are
accessible, validates package imports, and launches Streamlit with appropriate server settings
for both development and production environments.

Key Features:
    - Automatic Python path configuration for package discovery
    - Import validation with detailed error reporting
    - Environment-specific Streamlit configuration
    - Debug output for troubleshooting deployment issues
    - Cross-platform compatibility for different deployment scenarios

Environment Variables:
    STREAMLIT_ENV: When set to "development", enables additional development features
                   like automatic reloading on file changes (runOnSave)

Usage:
    Run directly as a Python script:
        python run_app.py
        
    Or as an executable (with proper shebang):
        ./run_app.py

Server Configuration:
    - Default address: 0.0.0.0 (accessible from all network interfaces)
    - Default port: 8501
    - Development mode: Automatic reload on file changes when STREAMLIT_ENV=development

Dependencies:
    streamlit: Web application framework and CLI
    app: Local application package containing the main Streamlit application

Note:
    This launcher is particularly useful in containerized environments where Python path
    configuration may be complex, or when the application needs to be launched with
    specific Streamlit server settings that differ from defaults.
"""

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
    
    # Ensure the app directory is in the Python path for imports
    app_dir = os.path.join(current_dir, "app")
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    
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