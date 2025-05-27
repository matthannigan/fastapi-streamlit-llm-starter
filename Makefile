.PHONY: help install test test-backend test-frontend test-coverage lint lint-backend lint-frontend format clean docker-build docker-up docker-down dev prod logs redis-cli backup restore

# Python executable detection
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

# Check if we're in a virtual environment or Docker
IN_VENV := $(shell $(PYTHON) -c "import sys; print('1' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '0')" 2>/dev/null || echo "0")
IN_DOCKER := $(shell [ -f /.dockerenv ] && echo "1" || echo "0")

# Use venv python if available and not in Docker, otherwise use system python
ifeq ($(IN_DOCKER),1)
    PYTHON_CMD := python
else ifeq ($(wildcard $(VENV_PYTHON)),$(VENV_PYTHON))
    PYTHON_CMD := $(VENV_PYTHON)
else
    PYTHON_CMD := $(PYTHON)
endif

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup and Testing:"
	@echo "  venv             Create virtual environment"
	@echo "  install          Install all dependencies (creates venv automatically)"
	@echo "  test             Run all tests (with Docker if available)"
	@echo "  test-local       Run tests without Docker dependency"
	@echo "  test-backend     Run backend tests only"
	@echo "  test-frontend    Run frontend tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  lint             Run code quality checks"
	@echo "  lint-backend     Run backend code quality checks only"
	@echo "  lint-frontend    Run frontend code quality checks only"
	@echo "  format           Format code with black and isort"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build     Build Docker images"
	@echo "  docker-up        Start services with Docker Compose"
	@echo "  docker-down      Stop Docker services"
	@echo "  dev              Start development environment"
	@echo "  prod             Start production environment"
	@echo "  logs             Show Docker Compose logs"
	@echo "  status           Show status of all services"
	@echo "  health           Check health of all services"
	@echo ""
	@echo "Utilities:"
	@echo "  redis-cli        Access Redis CLI"
	@echo "  backup           Backup Redis data"
	@echo "  restore          Restore Redis data"
	@echo "  clean            Clean up generated files"
	@echo "  clean-all        Clean up including virtual environment"

# Virtual environment setup
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip
	@echo "Virtual environment created at $(VENV_DIR)"
	@echo "To activate: source $(VENV_DIR)/bin/activate"

# Installation with venv support
install: venv
	@echo "Installing backend dependencies..."
	cd backend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	@echo "Installing frontend dependencies..."
	cd frontend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt

# Testing with proper Python command
test:
	@echo "Running all tests..."
	$(PYTHON_CMD) run_tests.py

test-backend:
	@echo "Running backend tests..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && $(PYTHON_CMD) -m pytest tests/ -v

test-coverage:
	@echo "Running tests with coverage..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	cd frontend && $(PYTHON_CMD) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Local testing without Docker
test-local: venv
	@echo "Running local tests without Docker..."
	@echo "Installing dependencies..."
	cd backend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	cd frontend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	@echo "Running backend tests..."
	cd backend && $(VENV_PYTHON) -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && $(VENV_PYTHON) -m pytest tests/ -v

# Code quality with proper Python command
lint:
	@echo "Running code quality checks..."
	@exit_code=0; \
	(cd backend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	(cd backend && $(PYTHON_CMD) -m mypy app/ --ignore-missing-imports) || exit_code=$$?; \
	(cd frontend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	exit $$exit_code

lint-backend:
	@echo "Running backend code quality checks..."
	@exit_code=0; \
	(cd backend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	(cd backend && $(PYTHON_CMD) -m mypy app/ --ignore-missing-imports) || exit_code=$$?; \
	exit $$exit_code

lint-frontend:
	@echo "Running frontend code quality checks..."
	cd frontend && $(PYTHON_CMD) -m flake8 app/

format:
	@echo "Formatting code..."
	cd backend && $(PYTHON_CMD) -m black app/ tests/
	cd backend && $(PYTHON_CMD) -m isort app/ tests/
	cd frontend && $(PYTHON_CMD) -m black app/ tests/
	cd frontend && $(PYTHON_CMD) -m isort app/ tests/

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

# Additional commands
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

logs:
	docker-compose logs -f

redis-cli:
	docker-compose exec redis redis-cli

backup:
	docker-compose exec redis redis-cli BGSAVE
	docker cp ai-text-processor-redis:/data/dump.rdb ./backups/redis-$(shell date +%Y%m%d-%H%M%S).rdb

restore:
	@if [ -z "$(BACKUP)" ]; then echo "Usage: make restore BACKUP=filename"; exit 1; fi
	docker cp ./backups/$(BACKUP) ai-text-processor-redis:/data/dump.rdb
	docker-compose restart redis

# Clean including venv
clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV_DIR) 