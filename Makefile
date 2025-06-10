.PHONY: help install test test-backend test-backend-slow test-backend-all test-backend-manual test-frontend test-integration test-coverage test-coverage-all test-retry test-circuit lint lint-backend lint-frontend format clean docker-build docker-up docker-down dev prod logs redis-cli backup restore repomix repomix-backend repomix-backend-tests repomix-frontend repomix-frontend-tests repomix-docs ci-test ci-test-all lock-deps update-deps list-presets show-preset validate-config validate-preset recommend-preset migrate-config test-presets

# Python executable detection
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

# Check if we're in a virtual environment or Docker
IN_VENV := $(shell $(PYTHON) -c "import sys; print('1' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '0')" 2>/dev/null || echo "0")
IN_DOCKER := $(shell [ -f /.dockerenv ] && echo "1" || echo "0")

# Use appropriate python command based on context
ifeq ($(IN_DOCKER),1)
    PYTHON_CMD := python
else ifeq ($(IN_VENV),1)
    PYTHON_CMD := python
else
    PYTHON_CMD := $(VENV_PYTHON)
endif

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup and Testing:"
	@echo "  venv                 Create backend virtual environment"
	@echo "  install              Install backend dependencies (creates venv automatically)"
	@echo "  install-frontend     Install frontend dependencies in Docker"
	@echo "  test                 Run all tests (with Docker if available)"
	@echo "  test-local           Run tests without Docker dependency"
	@echo "  test-backend         Run backend tests only (fast tests by default)"
	@echo "  test-backend-slow    Run slow backend tests only (requires --run-slow)"
	@echo "  test-backend-all     Run all backend tests (including slow ones)"
	@echo "  test-backend-manual  Run backend manual tests (requires --run-manual)"
	@echo "  test-frontend        Run frontend tests only"
	@echo "  test-integration     Run comprehensive integration tests"
	@echo "  test-coverage        Run tests with coverage report"
	@echo "  test-coverage-all    Run tests with coverage (including slow tests)"
	@echo "  test-retry           Run retry-specific tests only"
	@echo "  test-circuit         Run circuit breaker tests only"
	@echo "  ci-test              Run CI tests (fast tests only)"
	@echo "  ci-test-all          Run comprehensive CI tests (including slow tests)"
	@echo "  lint                 Run code quality checks"
	@echo "  lint-backend         Run backend code quality checks only"
	@echo "  lint-frontend        Run frontend code quality checks only"
	@echo "  format               Format code with black and isort"
	@echo "  lock-deps            Generate lock files from requirements"
	@echo "  update-deps          Update dependencies and regenerate lock files"
	@echo ""
	@echo "Resilience Configuration:"
	@echo "  list-presets         List available resilience configuration presets"
	@echo "  show-preset          Show details of a specific preset (PRESET=name)"
	@echo "  validate-config      Validate current resilience configuration"
	@echo "  validate-preset      Validate a specific preset configuration (PRESET=name)"
	@echo "  recommend-preset     Get preset recommendation for environment (ENV=name)"
	@echo "  migrate-config       Migrate legacy resilience configuration to presets"
	@echo "  test-presets         Run all preset-related tests"
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
	@echo "  clean-all        Clean up including virtual environments"
	@echo "  clean-venv       Clean up virtual environments only"
	@echo ""
	@echo "Documentation:"
	@echo "  repomix                Generate full repository documentation (excluding docs/)"
	@echo "  repomix-backend        Generate backend-only documentation (excluding tests)"
	@echo "  repomix-backend-tests  Generate backend-only tests documentation"
	@echo "  repomix-frontend       Generate frontend-only documentation (excluding tests)"
	@echo "  repomix-frontend-tests Generate frontend-only tests documentation"
	@echo "  repomix-docs           Generate documentation for README and docs/"

# Virtual environment setup (backend only)
venv:
	@echo "Creating backend virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip
	@echo "Backend virtual environment created at $(VENV_DIR)"
	@echo "To activate: source $(VENV_DIR)/bin/activate"

# Installation with backend venv and frontend Docker
install: venv
	@echo "Installing backend dependencies..."
	cd backend && source ../$(VENV_DIR)/bin/activate && pip install -r requirements.lock -r requirements-dev.lock

install-frontend:
	@echo "Frontend runs via Docker - no local installation needed"
	@echo "Use 'make dev-frontend' or 'make run-frontend' to start frontend"
	
# Testing with proper Python command
test:
	@echo "Running all tests..."
	$(PYTHON_CMD) scripts/run_tests.py

test-backend:
	@echo "Running backend tests (fast tests only, excluding manual tests)..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v

test-backend-slow:
	@echo "Running slow backend tests only..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "slow" --run-slow

test-backend-all:
	@echo "Running all backend tests (including slow ones, excluding manual tests)..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "not manual" --run-slow

test-backend-manual:
	@echo "Running backend manual tests..."
	@echo "⚠️  These tests require:"
	@echo "   - FastAPI server running on http://localhost:8000"
	@echo "   - API_KEY=test-api-key-12345 environment variable set"
	@echo "   - GEMINI_API_KEY environment variable set (for AI features)"
	@echo ""
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "manual" --run-manual

test-frontend:
	@echo "Running frontend tests via Docker..."
	docker-compose run frontend pytest tests/ -v

test-integration:
	@echo "Running comprehensive integration tests..."
	@echo "⚠️  Make sure both backend and frontend services are running first!"
	@echo "   Backend: http://localhost:8000"
	@echo "   Frontend: http://localhost:8501"
	@echo ""
	$(PYTHON_CMD) scripts/test_integration.py

test-coverage:
	@echo "Running tests with coverage (fast tests only, excluding manual tests)..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	docker-compose run frontend pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-coverage-all:
	@echo "Running tests with coverage (including slow tests, excluding manual tests)..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term -m "not manual" --run-slow
	docker-compose run frontend pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-retry:
	@echo "Running retry-specific tests only..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "retry" --run-slow

test-circuit:
	@echo "Running circuit breaker tests only..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "circuit_breaker" --run-slow

# Local testing without Docker
test-local: venv
	@echo "Running backend tests locally (frontend requires Docker)..."
	@echo "Installing backend dependencies..."
	cd backend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	@echo "Running backend tests..."
	cd backend && $(VENV_PYTHON) -m pytest tests/ -v
	@echo "Note: Frontend tests require Docker - use 'make test-frontend' instead"

# Code quality with proper Python command
lint:
	@echo "Running code quality checks..."
	@exit_code=0; \
	(cd backend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	(cd backend && $(PYTHON_CMD) -m mypy app/ --ignore-missing-imports) || exit_code=$$?; \
	(docker-compose run frontend flake8 app/) || exit_code=$$?; \
	exit $$exit_code

lint-backend:
	@echo "Running backend code quality checks..."
	@exit_code=0; \
	(cd backend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	(cd backend && $(PYTHON_CMD) -m mypy app/ --ignore-missing-imports) || exit_code=$$?; \
	exit $$exit_code

lint-frontend:
	@echo "Running frontend code quality checks via Docker..."
	docker-compose run frontend flake8 app/

format:
	@echo "Formatting code..."
	cd backend && $(PYTHON_CMD) -m black app/ tests/
	cd backend && $(PYTHON_CMD) -m isort app/ tests/
	docker-compose run frontend black app/ tests/
	docker-compose run frontend isort app/ tests/

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

# Clean venv only
clean-venv:
	@echo "Removing virtual environments..."
	rm -rf $(VENV_DIR)

# Clean everything (including venv)
clean-all: clean clean-venv
	@echo "Complete cleanup finished."

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

# Quick test for CI (fast tests only)
ci-test:
	@echo "Running CI tests (fast tests only)..."
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=xml
	cd frontend && python -m pytest tests/ -v --cov=app --cov-report=xml
	@echo "Running code quality checks..."
	cd backend && python -m flake8 app/
	cd frontend && python -m flake8 app/
	@echo "Validating resilience configuration..."
	python scripts/validate_resilience_config.py --validate-current --quiet

# Full CI test including slow tests (use for nightly builds or comprehensive testing)
ci-test-all:
	@echo "Running comprehensive CI tests (including slow tests)..."
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=xml -m "not manual" --run-slow
	cd frontend && python -m pytest tests/ -v --cov=app --cov-report=xml
	@echo "Running code quality checks..."
	cd backend && python -m flake8 app/
	cd frontend && python -m flake8 app/
	@echo "Running preset-related tests..."
	$(MAKE) test-presets
	@echo "Validating all presets..."
	python scripts/validate_resilience_config.py --validate-preset simple --quiet
	python scripts/validate_resilience_config.py --validate-preset development --quiet
	python scripts/validate_resilience_config.py --validate-preset production --quiet

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

health: ## Check health of all services including resilience configuration
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend unhealthy"
	@curl -f http://localhost:8501/_stcore/health || echo "Frontend unhealthy"
	@echo "Validating resilience configuration..."
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --validate-current --quiet || echo "Resilience configuration issues detected"

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

# Documentation generation with repomix
repomix:
	@echo "Generating full repository documentation..."
	npx repomix --ignore "docs/**/*"
	$(MAKE) repomix-backend
	$(MAKE) repomix-backend-tests
	$(MAKE) repomix-frontend  
	$(MAKE) repomix-frontend-tests
	$(MAKE) repomix-docs

repomix-backend:
	@echo "Generating backend documentation..."
	npx repomix --include "backend/**/*,shared/**/*,.env.example,README.md" --ignore "backend/tests/**/*" --output repomix-output_backend.md

repomix-backend-tests:
	@echo "Generating backend documentation..."
	npx repomix --include "backend/tests/**/*" --output repomix-output_backend-tests.md

repomix-frontend:
	@echo "Generating frontend documentation..."
	npx repomix --include "frontend/**/*,shared/**/*,.env.example,README.md" --ignore "frontend/tests/**/*"  --output repomix-output_frontend.md

repomix-frontend-tests:
	@echo "Generating frontend documentation..."
	npx repomix --include "frontend/tests/**/*"  --output repomix-output_frontend-tests.md

repomix-docs:
	@echo "Generating documentation for READMEs and docs/ subdirectory..."
	npx repomix --include "**/README.md,docs/**/*" --output repomix-output_docs.md

 ## Generate lock files from requirements (backend only - frontend uses Docker)
lock-deps: venv
	@echo "Generating backend lock files..."
	cd backend && $(PYTHON_CMD) -m piptools compile requirements.txt --output-file requirements.lock
	cd backend && $(PYTHON_CMD) -m piptools compile requirements-dev.txt --output-file requirements-dev.lock
	@echo "Note: Frontend dependencies are managed via Docker"

 ## Update dependencies and regenerate lock files (backend only - frontend uses Docker)
update-deps: venv
	@echo "Updating backend dependencies..."
	cd backend && $(PYTHON_CMD) -m piptools compile --upgrade requirements.txt --output-file requirements.lock
	cd backend && $(PYTHON_CMD) -m piptools compile --upgrade requirements-dev.txt --output-file requirements-dev.lock
	@echo "Note: Frontend dependencies are managed via Docker"

# Resilience preset management commands
list-presets:
	@echo "Available resilience configuration presets:"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --list-presets

show-preset:
	@if [ -z "$(PRESET)" ]; then echo "Usage: make show-preset PRESET=<preset_name>"; echo "Available presets: simple, development, production"; exit 1; fi
	@echo "Showing details for preset: $(PRESET)"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --show-preset $(PRESET)

validate-config:
	@echo "Validating current resilience configuration..."
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --validate-current

validate-preset:
	@if [ -z "$(PRESET)" ]; then echo "Usage: make validate-preset PRESET=<preset_name>"; echo "Available presets: simple, development, production"; exit 1; fi
	@echo "Validating preset: $(PRESET)"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --validate-preset $(PRESET)

recommend-preset:
	@if [ -z "$(ENV)" ]; then echo "Usage: make recommend-preset ENV=<environment>"; echo "Example environments: development, staging, production"; exit 1; fi
	@echo "Getting preset recommendation for environment: $(ENV)"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --recommend-preset $(ENV)

migrate-config:
	@echo "Analyzing legacy configuration and providing migration recommendations..."
	@$(PYTHON_CMD) scripts/migrate_resilience_config.py

test-presets:
	@echo "Running preset-related tests..."
	cd backend && $(PYTHON_CMD) -m pytest tests/unit/test_resilience_presets.py tests/integration/test_preset_resilience_integration.py -v
