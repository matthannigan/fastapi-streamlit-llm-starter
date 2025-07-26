#!/usr/bin/env python3
"""
Test runner script for the FastAPI-Streamlit-LLM starter template.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    """Main test runner."""
    print("FastAPI-Streamlit-LLM Starter Template Test Runner")
    print("=" * 60)
    
    # Get project root - scripts directory is in the project root
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    
    # Check if we're running in Docker or locally
    in_docker = os.environ.get('DOCKER_ENVIRONMENT', False)
    
    success_count = 0
    total_tests = 0
    
    # Backend tests
    if backend_dir.exists():
        print(f"\n🔧 Testing Backend ({backend_dir})")
        os.chdir(backend_dir)
        
        # Install dependencies
        if not in_docker:
            success = run_command(
                ["pip", "install", "-r", "requirements.txt"],
                "Installing backend dependencies"
            )
            if not success:
                print("❌ Failed to install backend dependencies")
                return 1
        
        # Run pytest with coverage
        test_commands = [
            (["python", "-m", "pytest", "tests/", "-v", "--ignore=tests/test_manual_api.py", "--ignore=tests/test_manual_auth.py"], "Running backend unit tests"),
            (["python", "-m", "pytest", "tests/", "--cov=app", "--cov-report=html", "--ignore=tests/test_manual_api.py", "--ignore=tests/test_manual_auth.py"], "Running backend tests with coverage"),
            (["python", "-m", "flake8", "app/"], "Running code style checks"),
            (["python", "-m", "mypy", "app/"], "Running type checking")
        ]
        
        for command, description in test_commands:
            total_tests += 1
            if run_command(command, description):
                success_count += 1
    
    # Frontend tests
    if frontend_dir.exists():
        print(f"\n🎨 Testing Frontend ({frontend_dir})")
        os.chdir(frontend_dir)
        
        # Install dependencies
        if not in_docker:
            success = run_command(
                ["pip", "install", "-r", "requirements.txt"],
                "Installing frontend dependencies"
            )
            if not success:
                print("❌ Failed to install frontend dependencies")
                return 1
        
        # Run pytest
        test_commands = [
            (["python", "-m", "pytest", "tests/", "-v"], "Running frontend unit tests"),
            (["python", "-m", "pytest", "tests/", "--cov=app"], "Running frontend tests with coverage"),
        ]
        
        for command, description in test_commands:
            total_tests += 1
            if run_command(command, description):
                success_count += 1
    
    # Integration tests (if Docker is available)
    os.chdir(project_root)
    if Path("docker-compose.yml").exists():
        print(f"\n🐳 Running Integration Tests")
        
        integration_commands = [
            (["docker-compose", "build"], "Building Docker images"),
            (["docker-compose", "up", "-d"], "Starting services"),
            (["sleep", "30"], "Waiting for services to start"),
            (["curl", "-f", "http://localhost:8000/health/"], "Testing backend health"),
            (["curl", "-f", "http://localhost:8501/_stcore/health/"], "Testing frontend health"),
            (["docker-compose", "down"], "Stopping services")
        ]
        
        for command, description in integration_commands:
            total_tests += 1
            if run_command(command, description):
                success_count += 1
    
    # Results summary
    print(f"\n{'='*60}")
    print(f"TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {success_count}/{total_tests}")
    print(f"❌ Failed: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"💥 {total_tests - success_count} test(s) failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 