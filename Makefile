.PHONY: help install test test-backend test-frontend test-coverage lint format clean docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install          Install all dependencies"
	@echo "  test             Run all tests"
	@echo "  test-backend     Run backend tests only"
	@echo "  test-frontend    Run frontend tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  lint             Run code quality checks"
	@echo "  format           Format code with black and isort"
	@echo "  clean            Clean up generated files"
	@echo "  docker-build     Build Docker images"
	@echo "  docker-up        Start services with Docker Compose"
	@echo "  docker-down      Stop Docker services"

# Installation
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt -r requirements-dev.txt
	@echo "Installing frontend dependencies..."
	cd frontend && pip install -r requirements.txt -r requirements-dev.txt

# Testing
test:
	@echo "Running all tests..."
	python run_tests.py

test-backend:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && python -m pytest tests/ -v

test-coverage:
	@echo "Running tests with coverage..."
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	cd frontend && python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Code quality
lint:
	@echo "Running code quality checks..."
	cd backend && python -m flake8 app/
	cd backend && python -m mypy app/ --ignore-missing-imports
	cd frontend && python -m flake8 app/

format:
	@echo "Formatting code..."
	cd backend && python -m black app/ tests/
	cd backend && python -m isort app/ tests/
	cd frontend && python -m black app/ tests/
	cd frontend && python -m isort app/ tests/

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting services..."
	docker-compose up -d

docker-down:
	@echo "Stopping services..."
	docker-compose down

# Development workflow
dev-setup: install
	@echo "Setting up development environment..."
	cd backend && pre-commit install
	@echo "Development environment ready!"

# Quick test for CI
ci-test:
	@echo "Running CI tests..."
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=xml
	cd frontend && python -m pytest tests/ -v --cov=app --cov-report=xml
	@echo "Running code quality checks..."
	cd backend && python -m flake8 app/
	cd frontend && python -m flake8 app/

# Additional Docker commands for development
restart: ## Restart all services
	docker-compose restart

backend-shell: ## Get shell access to backend container
	docker-compose exec backend /bin/bash

frontend-shell: ## Get shell access to frontend container
	docker-compose exec frontend /bin/bash

backend-logs: ## Show backend logs
	docker-compose logs -f backend

frontend-logs: ## Show frontend logs
	docker-compose logs -f frontend

status: ## Show status of all services
	docker-compose ps

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend unhealthy"
	@curl -f http://localhost:8501/_stcore/health || echo "Frontend unhealthy"

stop: ## Stop all services
	docker-compose stop 