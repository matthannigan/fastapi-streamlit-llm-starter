---
sidebar_label: run_app
---

# Launcher script for the Streamlit frontend with Python path configuration and debugging.

  file_path: `frontend/run_app.py`

This module serves as the entry point for running the Streamlit frontend application with proper
Python path setup and import resolution. It handles environment-specific configuration and
provides comprehensive debugging output for troubleshooting deployment issues.

The script automatically configures the Python path to ensure all application modules are
accessible, validates package imports, and launches Streamlit with appropriate server settings
for both development and production environments.

## Key Features

- Automatic Python path configuration for package discovery
- Import validation with detailed error reporting
- Environment-specific Streamlit configuration
- Debug output for troubleshooting deployment issues
- Cross-platform compatibility for different deployment scenarios

## Environment Variables

STREAMLIT_ENV: When set to "development", enables additional development features
like automatic reloading on file changes (runOnSave)

## Usage

Run directly as a Python script:
python run_app.py

Or as an executable (with proper shebang):
./run_app.py

## Server Configuration

- Default address: 0.0.0.0 (accessible from all network interfaces)
- Default port: 8501
- Development mode: Automatic reload on file changes when STREAMLIT_ENV=development

## Dependencies

streamlit: Web application framework and CLI
app: Local application package containing the main Streamlit application

## Note

This launcher is particularly useful in containerized environments where Python path
configuration may be complex, or when the application needs to be launched with
specific Streamlit server settings that differ from defaults.
