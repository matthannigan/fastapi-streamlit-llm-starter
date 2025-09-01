##################################################################################################
# FastAPI + Streamlit AI Text Processing Starter - Makefile
##################################################################################################
# This Makefile provides a comprehensive set of commands for developing, testing, and deploying
# the AI text processing application. Commands are organized into logical sections for easy navigation.
#
# Quick Start:
#   make help          - Show all available commands
#   make install       - Set up development environment  
#   make dev           - Start development servers
#   make test          - Run all tests
#   make lint          - Check code quality
#
# Requirements:
#   - Python 3.8+ for backend development
#   - Docker and Docker Compose for containerized development
#   - Node.js for repomix documentation generation (optional)
##################################################################################################

# Declare all targets as phony to avoid conflicts with files
.PHONY: help install run test lint format clean docker dev docs \
        venv install-frontend install-frontend-local run-backend \
        test-local test-backend test-backend-api test-backend-core test-backend-infrastructure \
        test-backend-integration test-backend-performance test-backend-services test-backend-schemas \
        test-backend-slow test-backend-all test-backend-manual test-frontend test-integration \
        test-coverage test-coverage-all test-retry test-circuit \
        lint-backend lint-frontend format \
        clean clean-venv clean-all \
        docker-build docker-up docker-down restart backend-shell frontend-shell \
        backend-logs frontend-logs status health stop \
        dev dev-legacy prod logs redis-cli backup restore \
				copy-readmes code_ref generate-doc-views \
				docusaurus docusaurus-serve docusaurus-build docusaurus-clear \
        mkdocs-serve mkdocs-build \
        repomix repomix-backend repomix-backend-tests repomix-frontend repomix-frontend-tests repomix-docs \
        ci-test ci-test-all lock-deps update-deps \
        list-presets show-preset validate-config validate-preset recommend-preset migrate-config test-presets \
        list-cache-presets show-cache-preset validate-cache-config validate-cache-preset recommend-cache-preset migrate-cache-config

##################################################################################################
# Configuration and Environment Detection
##################################################################################################

# Check if .env file exists and include it
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Example target to show the variables are loaded
show-env-vars:
	@echo "Backend Port is: $(BACKEND_PORT)"
	@echo "Frontend Port is: $(FRONTEND_PORT)"
	@echo "Redis Port is: $(REDIS_PORT)"
	@echo "Environment is: $(ENVIRONMENT)"
	@echo "Debug mode is: $(DEBUG)"
	@echo "Application logging level is: $(LOG_LEVEL)"
	@echo "---"
	@echo "The shell also sees BACKEND_PORT as: $$BACKEND_PORT etc"
		
# Python executable detection - prefer python3, fallback to python
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

# Git branch detection for branch-specific container naming
GIT_BRANCH := $(shell git branch --show-current 2>/dev/null | tr '/' '-' | tr '[:upper:]' '[:lower:]' || echo "main")
export GIT_BRANCH

# Assure unique container names
COMPOSE_PROJECT_NAME := llm-starter-$(GIT_BRANCH)
export COMPOSE_PROJECT_NAME

# Environment detection for smart Python command selection
IN_VENV := $(shell $(PYTHON) -c "import sys; print('1' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '0')" 2>/dev/null || echo "0")
IN_DOCKER := $(shell [ -f /.dockerenv ] && echo "1" || echo "0")

# Select appropriate Python command based on current environment
ifeq ($(IN_DOCKER),1)
    PYTHON_CMD := python
else ifeq ($(IN_VENV),1)
    PYTHON_CMD := python
else
    PYTHON_CMD := $(VENV_PYTHON)
endif

# Use custom repomix command if present in .env
REPOMIX_CMD ?= npx repomix
ifeq ($(strip $(REPOMIX_CMD)),)
REPOMIX_CMD := npx repomix
endif

##################################################################################################
# Help and Documentation
##################################################################################################

# Default target - show comprehensive help
help:
	@echo ""
	@echo "🚀 FastAPI + Streamlit AI Text Processing Starter"
	@echo "=================================================================="
	@echo ""
	@echo "📚 QUICK START COMMANDS:"
	@echo "  make install         📦 Set up complete development environment"
	@echo "  make dev             🔧 Start development servers (frontend + backend)"
	@echo "  make test            🧪 Run all tests (backend + frontend)"
	@echo "  make lint            🔍 Check code quality and formatting"
	@echo "  make clean           🧹 Clean up generated files and caches"
	@echo ""
	@echo "🏗️  SETUP AND INSTALLATION:"
	@echo "  venv                 Create Python virtual environment for backend"
	@echo "  install              Install backend dependencies (auto-creates venv)"
	@echo "  install-frontend     Install frontend dependencies via Docker"
	@echo "  install-frontend-local  Install frontend deps in current venv (local dev)"
	@echo ""
	@echo "🖥️  DEVELOPMENT SERVERS:"
	@echo "  run-backend          Start FastAPI server locally (http://localhost:8000)"
	@echo "  dev                  Start full development environment with hot reload"
	@echo "  dev-legacy           Start development environment (legacy mode)"
	@echo "  prod                 Start production environment"
	@echo ""
	@echo "🧪 TESTING COMMANDS:"
	@echo "  test                 Run all tests (backend + frontend with Docker)"
	@echo "  test-local           Run backend tests locally (no Docker required)"
	@echo "  test-backend         Run backend tests (fast tests only)"
	@echo "  test-backend-api     Run backend API endpoint tests"
	@echo "  test-backend-core    Run backend core functionality tests"
	@echo "  test-backend-infrastructure  Run all infrastructure service tests"
	@echo "  test-backend-infra   Run all infrastructure service tests (alias)"
	@echo "  test-backend-infra-ai        Run AI infrastructure service tests"
	@echo "  test-backend-infra-cache     Run cache infrastructure service tests"
	@echo "  test-backend-infra-monitoring Run monitoring infrastructure service tests"
	@echo "  test-backend-infra-resilience Run resilience infrastructure service tests"
	@echo "  test-backend-infra-security   Run security infrastructure service tests"
	@echo "  test-backend-integration     Run backend integration tests"
	@echo "  test-backend-performance    Run backend performance tests"
	@echo "  test-backend-services       Run domain services tests"
	@echo "  test-backend-schemas        Run shared schema tests"
	@echo "  test-backend-slow    Run slow/comprehensive backend tests"
	@echo "  test-backend-all     Run all backend tests (including slow tests)"
	@echo "  test-backend-manual  Run manual tests (requires running server)"
	@echo "  test-frontend        Run frontend tests via Docker"
	@echo "  test-integration     Run end-to-end integration tests"
	@echo "  test-coverage        Run tests with coverage reporting"
	@echo "  test-coverage-all    Run coverage including slow tests"
	@echo "  test-retry           Run retry mechanism tests"
	@echo "  test-circuit         Run circuit breaker tests"
	@echo ""
	@echo "🔍 CODE QUALITY:"
	@echo "  lint                 Run all code quality checks (backend + frontend)"
	@echo "  lint-backend         Run backend linting (flake8 + mypy)"
	@echo "  lint-frontend        Run frontend linting via Docker"
	@echo "  format               Format code with black and isort"
	@echo ""
	@echo "⚙️  RESILIENCE CONFIGURATION:"
	@echo "  list-presets         List available resilience presets"
	@echo "  show-preset          Show preset details (Usage: PRESET=simple)"
	@echo "  validate-config      Validate current resilience configuration"
	@echo "  validate-preset      Validate specific preset (Usage: PRESET=simple)"
	@echo "  recommend-preset     Get preset recommendation (Usage: ENV=development)"
	@echo "  migrate-config       Migrate legacy config to presets"
	@echo "  test-presets         Run all preset-related tests"
	@echo ""
	@echo "🗂️  CACHE CONFIGURATION:"
	@echo "  list-cache-presets   List available cache presets"
	@echo "  show-cache-preset    Show cache preset details (Usage: PRESET=development)"
	@echo "  validate-cache-config Validate current cache configuration"
	@echo "  validate-cache-preset Validate specific cache preset (Usage: PRESET=production)"
	@echo "  recommend-cache-preset Get cache preset recommendation (Usage: ENV=staging)"
	@echo "  migrate-cache-config Migrate legacy cache config to presets"
	@echo ""
	@echo "🐳 DOCKER OPERATIONS:"
	@echo "  docker-build         Build all Docker images"
	@echo "  docker-up            Start services with Docker Compose"
	@echo "  docker-down          Stop and remove Docker services"
	@echo "  restart              Restart all Docker services"
	@echo "  backend-shell        Open shell in backend container"
	@echo "  frontend-shell       Open shell in frontend container"
	@echo "  backend-logs         Show backend container logs"
	@echo "  frontend-logs        Show frontend container logs"
	@echo "  logs                 Show all service logs"
	@echo "  status               Show status of all services"
	@echo "  health               Check health of all services"
	@echo "  stop                 Stop all services"
	@echo ""
	@echo "🗄️  DATA MANAGEMENT:"
	@echo "  redis-cli            Access Redis command line interface"
	@echo "  backup               Backup Redis data with timestamp"
	@echo "  restore              Restore Redis data (Usage: BACKUP=filename)"
	@echo ""
	@echo "🧹 CLEANUP:"
	@echo "  clean                Clean Python cache files and test artifacts"
	@echo "  clean-venv           Remove virtual environment"
	@echo "  clean-all            Complete cleanup (cache + venv)"
	@echo ""
	@echo "📖 DOCUMENTATION:"
	@echo "  code_ref             Generate code reference documentation"
	@echo "  generate-doc-views   Generate BY_TOPIC.md and BY_AUDIENCE.md from metadata"
	@echo ""
	@echo "📚 DOCUMENTATION WEBSITES:"
	@echo "  docusaurus           Serve Docusaurus documentation locally"
	@echo "  docusaurus-build     Build static Docusaurus documentation site"
	@echo "  docusaurus-serve     Serve built Docusaurus site"
	@echo "  docusaurus-clear     Clear Docusaurus build cache"
	@echo "  docusaurus-install   Install Docusaurus dependencies"
	@echo "  mkdocs-serve         Serve MkDocs documentation locally (http://127.0.0.1:8000)"
	@echo "  mkdocs-build         Build static MkDocs documentation site"
	@echo ""
	@echo "📄 REPOSITORY DOCUMENTATION (Repomix):"
	@echo "  repomix              Generate complete repository documentation"
	@echo "  repomix-backend      Generate backend-only documentation"
	@echo "  repomix-backend-tests Generate backend tests documentation"
	@echo "  repomix-frontend     Generate frontend-only documentation"
	@echo "  repomix-frontend-tests Generate frontend tests documentation"
	@echo "  repomix-docs         Generate README and docs/ documentation"
	@echo ""
	@echo "🏭 CI/CD AND DEPENDENCIES:"
	@echo "  ci-test              Run fast CI tests (for pull requests)"
	@echo "  ci-test-all          Run comprehensive CI tests (for releases)"
	@echo "  lock-deps            Generate dependency lock files"
	@echo "  update-deps          Update and lock dependencies"
	@echo ""
	@echo "💡 EXAMPLES:"
	@echo "  make install && make dev    # Complete setup and start development"
	@echo "  make test-backend-api       # Test just the API endpoints"
	@echo "  make test-backend-infra-cache # Test just cache infrastructure"
	@echo "  make show-preset PRESET=production  # Show production preset"
	@echo "  make restore BACKUP=redis-20240101-120000.rdb  # Restore backup"
	@echo "  make code_ref && make docusaurus # Generate docs and serve locally"
	@echo ""
	@echo "📝 For detailed documentation, see README.md and docs/ directory"
	@echo ""

##################################################################################################
# Setup and Installation
##################################################################################################

# Create Python virtual environment for backend development
venv:
	@echo "🔧 Creating backend virtual environment..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
		$(VENV_PIP) install --upgrade pip; \
		echo "✅ Backend virtual environment created at $(VENV_DIR)"; \
		echo "💡 To activate: source $(VENV_DIR)/bin/activate"; \
	else \
		echo "ℹ️  Virtual environment already exists at $(VENV_DIR)"; \
	fi

# Install backend dependencies (auto-creates venv)
install: venv docusaurus-install
	@echo "📦 Installing backend dependencies..."
	@cd backend && source ../$(VENV_DIR)/bin/activate && pip install -r requirements.lock -r requirements-dev.lock
	@echo "✅ Backend dependencies installed successfully!"
	@echo "✅ project venv activated via: source $(VENV_DIR)/bin/activate"
	@echo "💡 Next steps:"
	@echo "   - make run-backend    # Start backend server"
	@echo "   - make dev            # Start full development environment"

# Install frontend dependencies via Docker (recommended)
install-frontend:
	@echo "ℹ️  Frontend dependencies are managed via Docker for consistency"
	@echo "💡 Recommended commands:"
	@echo "   - make dev           # Start full development environment"
	@echo "   - make test-frontend # Run frontend tests"
	@echo ""
	@echo "🔧 For local development without Docker, use: make install-frontend-local"

# Install frontend dependencies in current virtual environment (local development)
install-frontend-local:
	@echo "📦 Installing frontend Python dependencies into current virtual environment..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "❌ Error: No virtual environment detected"; \
		echo "   Please activate your virtual environment first:"; \
		echo "   source .venv/bin/activate"; \
		exit 1; \
	fi
	@echo "🔧 Installing frontend dependencies..."
	@cd frontend && pip install -r requirements.txt -r requirements-dev.txt
	@echo "✅ Frontend dependencies installed successfully!"
	@echo "💡 You can still use Docker with 'make dev' for full containerized development"

##################################################################################################
# Development Servers
##################################################################################################

# Start backend FastAPI server locally with auto-reload
run-backend:
	@echo "🚀 Starting backend FastAPI server..."
	@echo ""
	@echo "📍 Server endpoints:"
	@echo "   🌐 API Documentation (Swagger): $(API_BASE_URL)/docs"
	@echo "   📚 API Documentation (ReDoc):   $(API_BASE_URL)/redoc"
	@echo "   🔌 API Base URL:                $(API_BASE_URL)"
	@echo "   ❤️  Health Check:               $(API_BASE_URL)/health"
	@echo ""
	@echo "⏹️  Press Ctrl+C to stop the server"
	@echo ""
	@cd backend && $(PYTHON_CMD) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start full development environment with hot reload (Docker Compose v2.22+)
dev:
	@echo "🚀 Starting development environment..."
	@echo "📍 Services will be available at:"
	@echo "   🌐 Frontend (Streamlit): http://localhost:$(FRONTEND_PORT)"
	@echo "   🔌 Backend (FastAPI):    http://localhost:$(BACKEND_PORT)"
	@echo "   🗄️  Redis:               localhost:$(REDIS_PORT)"
	@echo ""
	@echo "💡 File watching enabled - changes will trigger automatic reloads"
	@echo "⏹️  Press Ctrl+C to stop all services"
	@echo ""
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build --watch

# Start development environment (legacy mode for older Docker Compose)
dev-legacy:
	@echo "🚀 Starting development environment (legacy mode)..."
	@echo "📍 Services will be available at:"
	@echo "   🌐 Frontend (Streamlit): http://localhost:$(FRONTEND_PORT)"
	@echo "   🔌 Backend (FastAPI):    http://localhost:$(BACKEND_PORT)"
	@echo "   🗄️  Redis:               localhost:$(REDIS_PORT)"
	@echo ""
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Start production environment
prod:
	@echo "🏭 Starting production environment..."
	@echo "⚠️  Production mode - no auto-reload, optimized builds"
	@echo ""
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	@echo "✅ Production services started in background"
	@echo "💡 Use 'make logs' to view logs, 'make status' to check status"

##################################################################################################
# Testing Commands
##################################################################################################
# Run all tests (backend + frontend with Docker)
test:
	@echo "🧪 Running all tests (backend + frontend)..."
	@echo "💡 This runs the comprehensive test suite"
	@$(PYTHON_CMD) scripts/run_tests.py

# Run backend tests locally without Docker
test-local: venv
	@echo "🧪 Running backend tests locally (no Docker required)..."
	@echo "📦 Installing backend dependencies..."
	@cd backend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	@echo "🔬 Running backend tests..."
	@cd backend && $(VENV_PYTHON) -m pytest tests/ -v
	@echo "ℹ️  Note: Frontend tests require Docker - use 'make test-frontend'"

##################################################################################################
# Backend Testing (Granular)
##################################################################################################

# Run backend tests (fast tests only, default)
test-backend:
	@echo "🧪 Running backend tests (fast tests only)..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/ -q --retries 2 --retry-delay 5

# Run backend API endpoint tests
test-backend-api:
	@echo "🧪 Running backend API endpoint tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/api/ -v

# Run backend core functionality tests
test-backend-core:
	@echo "🧪 Running backend core functionality tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/core/ -v

# Run infrastructure service tests
test-backend-infra:
	@echo "🧪 Running backend infrastructure service tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/ -v

# Run infrastructure service tests
test-backend-infra-ai:
	@echo "🧪 Running backend AI infrastructure service tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/ai/ -v

# Run infrastructure service tests
test-backend-infra-cache:
#	@echo "🧪 Running backend cache infrastructure service tests that use redis..."
#	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/cache/ -m "redis" -n 0 -q --retries 2 --retry-delay 5
#	@echo "🧪 Running backend cache infrastructure service tests (excluding redis tests)..."
	@echo "🧪 Running backend cache infrastructure service tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/cache/ -n auto -q --tb=no

# Run infrastructure service tests
test-backend-infra-monitoring:
	@echo "🧪 Running backend monitoring infrastructure service tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/monitoring/ -v

# Run infrastructure service tests
test-backend-infra-resilience:
	@echo "🧪 Running backend resilience infrastructure service tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/resilience/ -v

# Run infrastructure service tests
test-backend-infra-security:
	@echo "🧪 Running backend security infrastructure service tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/security/ -v

# Run backend integration tests
test-backend-integration:
	@echo "🧪 Running backend integration tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/integration/ -v

# Run backend performance tests
test-backend-performance:
	@echo "🧪 Running backend performance tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/performance/ -v

# Run domain services tests
test-backend-services:
	@echo "🧪 Running backend domain services tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/services/ -v

# Run shared schema tests
test-backend-schemas:
	@echo "🧪 Running backend shared schema tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/shared_schemas/ -v

# Run slow/comprehensive backend tests
test-backend-slow:
	@echo "🧪 Running slow backend tests (comprehensive)..."
	@echo "⏳ This may take several minutes..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "slow" --run-slow --timeout=60

# Run all backend tests including slow ones
test-backend-all:
	@echo "🧪 Running ALL backend tests (including slow tests)..."
	@echo "⏳ This may take several minutes..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "not manual" --run-slow --timeout=60

# Run manual tests (require running server)
test-backend-manual:
	@echo "🧪 Running backend manual tests..."
	@echo "⚠️  Prerequisites for manual tests:"
	@echo "   ✅ FastAPI server running: http://localhost:$(BACKEND_PORT)"
	@echo "   ✅ Environment variables set:"
	@echo "      - API_KEY=test-api-key-12345"
	@echo "      - GEMINI_API_KEY=<your-gemini-api-key>"
	@echo ""
	@echo "💡 Start server first: make run-backend"
	@echo ""
	@cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "manual" --run-manual --timeout=60

##################################################################################################
# Frontend and Integration Testing
##################################################################################################

# Run frontend tests via Docker
test-frontend:
	@echo "🧪 Running frontend tests via Docker..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml run frontend pytest tests/ -v

# Run end-to-end integration tests
test-integration:
	@echo "🧪 Running comprehensive integration tests..."
	@echo "⚠️  Prerequisites:"
	@echo "   ✅ Backend running: http://localhost:$(BACKEND_PORT)"
	@echo "   ✅ Frontend running: http://localhost:$(FRONTEND_PORT)"
	@echo ""
	@echo "💡 Start services first: make dev"
	@echo ""
	@$(PYTHON_CMD) scripts/test_integration.py

##################################################################################################
# Coverage and Specialized Testing
##################################################################################################

# Run tests with coverage reporting
test-coverage:
	@echo "🧪 Running tests with coverage reporting..."
	@echo "📊 Generating coverage reports for backend and frontend..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term --timeout=60
	@docker-compose run frontend pytest tests/ -v --cov=app --cov-report=html --cov-report=term --timeout=60
	@echo "📁 Coverage reports generated in htmlcov/ directories"

# Run coverage including slow tests
test-coverage-all:
	@echo "🧪 Running comprehensive coverage (including slow tests)..."
	@echo "⏳ This may take several minutes..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term -m "not manual" --run-slow --timeout=60
	@docker-compose run frontend pytest tests/ -v --cov=app --cov-report=html --cov-report=term --timeout=60

# Run retry mechanism tests
test-retry:
	@echo "🧪 Running retry mechanism tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "retry" --run-slow --timeout=60

# Run circuit breaker tests
test-circuit:
	@echo "🧪 Running circuit breaker tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "circuit_breaker" --run-slow --timeout=60

##################################################################################################
# Code Quality and Formatting
##################################################################################################

# Run all code quality checks (backend + frontend)
lint:
	@echo "🔍 Running comprehensive code quality checks..."
	@echo "📋 Checking backend (flake8 + mypy)..."
	@exit_code=0; \
	(cd backend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	(cd backend && $(PYTHON_CMD) -m mypy app/ --ignore-missing-imports) || exit_code=$$?; \
	echo "📋 Checking frontend via Docker..."; \
	(docker-compose run frontend flake8 app/) || exit_code=$$?; \
	if [ $$exit_code -eq 0 ]; then \
		echo "✅ All code quality checks passed!"; \
	else \
		echo "❌ Code quality issues found"; \
	fi; \
	exit $$exit_code

# Run backend code quality checks only
lint-backend:
	@echo "🔍 Running backend code quality checks..."
	@exit_code=0; \
	echo "📋 Running flake8..."; \
	(cd backend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	echo "📋 Running mypy..."; \
	(cd backend && $(PYTHON_CMD) -m mypy app/ --ignore-missing-imports) || exit_code=$$?; \
	if [ $$exit_code -eq 0 ]; then \
		echo "✅ Backend code quality checks passed!"; \
	else \
		echo "❌ Backend code quality issues found"; \
	fi; \
	exit $$exit_code

# Run frontend code quality checks via Docker
lint-frontend:
	@echo "🔍 Running frontend code quality checks via Docker..."
	@docker-compose run frontend flake8 app/

# Lint a specific file
lint-file:
	@if [ -z "$(FILE)" ]; then echo "Usage: make lint-file FILE=path/to/file.py"; exit 1; fi
	@echo "🔍 Linting $(FILE)..."
	@source $(VENV_DIR)/bin/activate && $(PYTHON_CMD) -m flake8 "$(FILE)"
	@echo "🔍 Type checking $(FILE)..."
	@source $(VENV_DIR)/bin/activate && $(PYTHON_CMD) -m mypy "$(FILE)" --ignore-missing-imports || true

# Format code with black and isort
format:
	@echo "🎨 Formatting code with black and isort..."
	@echo "📝 Formatting backend..."
	@cd backend && $(PYTHON_CMD) -m black app/ tests/
	@cd backend && $(PYTHON_CMD) -m isort app/ tests/
	@echo "📝 Formatting frontend via Docker..."
	@docker-compose run frontend black app/ tests/
	@docker-compose run frontend isort app/ tests/
	@echo "✅ Code formatting complete!"

##################################################################################################
# Cleanup Commands
##################################################################################################

# Clean Python cache files and test artifacts
clean:
	@echo "🧹 Cleaning up generated files and caches..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".coverage" -delete 2>/dev/null || true
	@find . -name "coverage.xml" -delete 2>/dev/null || true
	@./backend/scripts/clean_redis_test_env.sh
	@echo "✅ Cleanup complete!"

# Remove virtual environment only
clean-venv:
	@echo "🧹 Removing virtual environment..."
	@rm -rf $(VENV_DIR)
	@echo "✅ Virtual environment removed!"

# Complete cleanup (cache + venv)
clean-all: clean clean-venv
	@echo "🧹 Complete cleanup finished!"

##################################################################################################
# Docker Operations
##################################################################################################

# Build all Docker images
docker-build:
	@echo "🐳 Building Docker images..."
	@docker-compose build
	@echo "✅ Docker images built successfully!"

# Start services with Docker Compose
docker-up:
	@echo "🐳 Starting services with Docker Compose..."
	@docker-compose up -d
	@echo "✅ Services started! Use 'make status' to check status"

# Stop and remove Docker services
docker-down:
	@echo "🐳 Stopping Docker services..."
	@docker-compose down
	@echo "✅ Services stopped!"

# Restart all Docker services
restart:
	@echo "🔄 Restarting all Docker services..."
	@docker-compose restart
	@echo "✅ Services restarted!"

# Get shell access to backend container
backend-shell:
	@echo "🐚 Opening shell in backend container..."
	@docker-compose exec backend /bin/bash

# Get shell access to frontend container
frontend-shell:
	@echo "🐚 Opening shell in frontend container..."
	@docker-compose exec frontend /bin/bash

# Show backend container logs
backend-logs:
	@echo "📋 Showing backend logs (Ctrl+C to exit)..."
	@docker-compose logs -f backend

# Show frontend container logs
frontend-logs:
	@echo "📋 Showing frontend logs (Ctrl+C to exit)..."
	@docker-compose logs -f frontend

# Show all service logs
logs:
	@echo "📋 Showing all service logs (Ctrl+C to exit)..."
	@docker-compose logs -f

# Show status of all services
status:
	@echo "📊 Docker services status:"
	@docker-compose ps

# Check health of all services
health:
	@echo "❤️  Checking service health..."
	@echo "🔌 Backend health:"
	@curl -f http://localhost:$(BACKEND_PORT)/health 2>/dev/null && echo "✅ Backend healthy" || echo "❌ Backend unhealthy"
	@echo "🌐 Frontend health:"
	@curl -f http://localhost:$(FRONTEND_PORT)/_stcore/health 2>/dev/null && echo "✅ Frontend healthy" || echo "❌ Frontend unhealthy"
	@echo "⚙️  Resilience configuration:"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --validate-current --quiet 2>/dev/null && echo "✅ Configuration valid" || echo "❌ Configuration issues detected"

# Stop all services
stop:
	@echo "⏹️  Stopping all services..."
	@docker-compose stop
	@echo "✅ All services stopped!"

##################################################################################################
# Data Management
##################################################################################################

# Access Redis command line interface
redis-cli:
	@echo "🗄️  Opening Redis CLI..."
	@docker-compose exec redis redis-cli

# Backup Redis data with timestamp
backup:
	@echo "💾 Creating Redis backup..."
	@docker-compose exec redis redis-cli BGSAVE
	@mkdir -p ./backups
	@docker cp llm-starter-redis-$${GIT_BRANCH:-main}:/data/dump.rdb ./backups/redis-$(shell date +%Y%m%d-%H%M%S).rdb
	@echo "✅ Backup created in ./backups/"

# Restore Redis data from backup
restore:
	@if [ -z "$(BACKUP)" ]; then \
		echo "❌ Usage: make restore BACKUP=filename"; \
		echo "💡 Example: make restore BACKUP=redis-20240101-120000.rdb"; \
		echo "📁 Available backups:"; \
		ls -la ./backups/ 2>/dev/null || echo "   No backups found"; \
		exit 1; \
	fi
	@echo "🔄 Restoring Redis data from $(BACKUP)..."
	@docker cp ./backups/$(BACKUP) llm-starter-redis-$${GIT_BRANCH:-main}:/data/dump.rdb
	@docker-compose restart redis
	@echo "✅ Redis data restored from $(BACKUP)!"

##################################################################################################
# Documentation Scripts
##################################################################################################

# Copy all READMEs saved within the codebase to docs/quick-guides
#copy-readmes:
#	@cp README.md docs/README.md
#	@mkdir -p docs/READMEs
#	@find backend -name "README.md" -type f -exec sh -c 'mkdir -p "docs/READMEs/$$(dirname "$$1")" && cp "$$1" "docs/READMEs/$$1"' _ {} \;
#	@find frontend -name "README.md" -type f -exec sh -c 'mkdir -p "docs/READMEs/$$(dirname "$$1")" && cp "$$1" "docs/READMEs/$$1"' _ {} \;
#	@find shared -name "README.md" -type f -exec sh -c 'mkdir -p "docs/READMEs/$$(dirname "$$1")" && cp "$$1" "docs/READMEs/$$1"' _ {} \;
#	@find examples -name "README.md" -type f -exec sh -c 'mkdir -p "docs/READMEs/$$(dirname "$$1")" && cp "$$1" "docs/READMEs/$$1"' _ {} \;
#	@find scripts -name "README.md" -type f -exec sh -c 'mkdir -p "docs/READMEs/$$(dirname "$$1")" && cp "$$1" "docs/READMEs/$$1"' _ {} \;
#	@echo "✅ READMEs copied to docs/READMEs/"

# Export docstrings from codebase to docs/code_ref
code_ref:
	@cp README.md docs/README.md
	@echo "✅ Repository README copied to docs/README"
	@rm -Rf docs/code_ref/backend/  && mkdir docs/code_ref/backend/  && $(PYTHON_CMD) scripts/generate_code_docs.py backend/  --md-output-dir docs/code_ref/backend/
	@rm -Rf docs/code_ref/frontend/ && mkdir docs/code_ref/frontend/ && $(PYTHON_CMD) scripts/generate_code_docs.py frontend/ --md-output-dir docs/code_ref/frontend/
	@rm -Rf docs/code_ref/shared/   && mkdir docs/code_ref/shared/   && $(PYTHON_CMD) scripts/generate_code_docs.py shared/shared/   --md-output-dir docs/code_ref/shared/
	@rm -Rf docs/code_ref/examples/ && mkdir docs/code_ref/examples/ && $(PYTHON_CMD) scripts/generate_code_docs.py examples/ --md-output-dir docs/code_ref/examples/
	@rm -Rf docs/code_ref/scripts/  && mkdir docs/code_ref/scripts/  && $(PYTHON_CMD) scripts/generate_code_docs.py scripts/  --md-output-dir docs/code_ref/scripts/
	@echo "✅ docstrings copied to docs/code_ref/"

# Generate alternative documentation views from metadata
generate-doc-views:
	@echo "📄 Generating documentation views from metadata..."
	@$(PYTHON_CMD) scripts/generate_doc_views.py
#	@echo "✅ Documentation views generated: docs/BY_TOPIC.md and docs/BY_AUDIENCE.md"

# Generate public contracts
generate-contracts:
	@echo "📄 Generating .pyi public contracts for backend..."
	@find backend/contracts -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + && $(PYTHON_CMD) scripts/generate_code_docs.py backend/app/ --pyi-output-dir backend/contracts/

##################################################################################################
# Documentation Website (via Docusaurus)
##################################################################################################

docusaurus: code_ref
	@echo "📖 Serving documentation locally..."
	@echo "⏹️  Press Ctrl+C to stop"
	cd docs-website && npm run start

docusaurus-build: code_ref
	@echo "📖 Building static documentation site..."
	cd docs-website && npm run build
	@echo "✅ Documentation built in docs-website/build/"

docusaurus-serve: docusaurus-build
	cd docs-website && npm run serve

docusaurus-clear:
	cd docs-website && npm run clear

docusaurus-install:
	@echo "📦 Installing Docusaurus at docs-website/..."
	cd docs-website && npm install

##################################################################################################
# Documentation Website (via Mkdocs)
##################################################################################################

# Serve documentation locally for development
mkdocs-serve:
	@echo "📖 Serving documentation locally..."
	@echo "🌐 Documentation available at: http://127.0.0.1:8000"
	@echo "⏹️  Press Ctrl+C to stop"
	@mkdocs serve

# Build static documentation site
mkdocs-build:
	@echo "📖 Building static documentation site..."
	@mkdocs build --clean
	@echo "✅ Documentation built in site/ directory"

##################################################################################################
# Documentation Export (Repomix)
##################################################################################################

# Generate complete repository documentation
repomix:
	@echo "📄 Generating comprehensive repository documentation..."
	@mkdir -p repomix-output
	@echo "📝 Creating full repository uncompressed documentation..."
	@$(REPOMIX_CMD) --output repomix-output/repomix_ALL_U.md --quiet --ignore "docs/code_ref*/**/*,**/contracts/**/*"
	@echo "📝 Creating full repository compressed documentation..."
	@$(REPOMIX_CMD) --output repomix-output/repomix_ALL_C.md --quiet --ignore "docs/code_ref*/**/*,**/contracts/**/*" --compress
	@$(MAKE) repomix-backend
	@$(MAKE) repomix-frontend  
	@$(MAKE) repomix-docs
	@echo "✅ All repository documentation generated in repomix-output/"

# Generate backend main documentation
repomix-backend:
	@echo "📄 Generating backend documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-ALL_U.md --quiet --include "backend/**/*,shared/**/*,.env.example*,docs/guides/application/BACKEND.md" --ignore "backend/contracts/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-app_U.md --quiet --include "backend/**/*,shared/**/*,.env.example*,docs/guides/application/BACKEND.md" --ignore "backend/contracts/**/*,backend/examples/**/*,backend/scripts/**/*,backend/tests/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-app_C.md --quiet --include "backend/**/*,shared/**/*,.env.example*,docs/guides/application/BACKEND.md" --ignore "backend/contracts/**/*,backend/examples/**/*,backend/scripts/**/*,backend/tests/**/*" --compress

# Generate backend tests documentation
repomix-backend-tests:
	@echo "📄 Generating backend tests documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-test_U.md --quiet --include "backend/tests/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-test_C.md --quiet --include "backend/tests/**/*" --compress

# Generate backend cache documentation 
repomix-backend-cache:
	@echo "📄 Generating backend cache documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-cache_U.md --quiet --include "backend/**/cache/**/*,backend/**/*cache*.*,backend/**/*CACHE*.*,.env.example,docs/guides/application/BACKEND.md,docs/**/cache/**/*,docs/**/*cache*.*" --ignore "backend/contracts/**/*,docs/code_ref/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-cache_C.md --quiet --include "backend/**/cache/**/*,backend/**/*cache*.*,backend/**/*CACHE*.*,.env.example,docs/guides/application/BACKEND.md,docs/**/cache/**/*,docs/**/*cache*.*" --ignore "backend/contracts/**/*,docs/code_ref/**/*" --compress

# Generate backend contracts documentation 
repomix-backend-contracts:
	@echo "📄 Generating backend cache documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-contracts_U.md --quiet --no-file-summary --header-text "$$(cat backend/contracts/repomix-instructions.md)" --include "backend/contracts/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-contracts-cache_U.md --quiet --no-file-summary --header-text "$$(cat backend/contracts/repomix-instructions.md)" --include "backend/contracts/**/cache/**/*,backend/contracts/**/*cache*.*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-contracts-resilience_U.md --quiet --no-file-summary --header-text "$$(cat backend/contracts/repomix-instructions.md)" --include "backend/contracts/**/resilience/**/*,backend/contracts/**/*resilience*.*"

repomix-backend-tests-cache:
	@echo "📄 Generating backend tests cache documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-tests-cache_U.md --quiet --include "backend/tests/**/cache/**/*,backend/tests/**/*cache*.*"

repomix-backend-tests-cache-fixtures:
	@echo "📄 Generating backend tests cache fixtures documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-tests-cache-fixtures_U.md --quiet --include "backend/tests/infrastructure/cache/**/conftest.py"

# Generate frontend-only documentation
repomix-frontend:
	@echo "📄 Generating frontend documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_frontend-ALL_U.md --quiet --include "frontend/**/*,shared/**/*,.env.example,frontend/README.md"
	@$(REPOMIX_CMD) --output repomix-output/repomix_frontend-app_C.md --quiet --include "frontend/**/*,shared/**/*,.env.example,frontend/README.md" --ignore "frontend/tests/**/*"  --compress
	@$(REPOMIX_CMD) --output repomix-output/repomix_frontend-app_U.md --quiet --include "frontend/**/*,shared/**/*,.env.example,frontend/README.md" --ignore "frontend/tests/**/*"

# Generate frontend tests documentation
repomix-frontend-tests:
	@echo "📄 Generating frontend tests documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_frontend-tests_U.md --quiet --include "frontend/tests/**/*"

# Generate documentation for code_ref, READMEs and docs/
repomix-docs: generate-doc-views
	@echo "📄 Generating documentation for READMEs and docs/..."
	@mkdir -p repomix-output
#	@$(REPOMIX_CMD) --output repomix-output/repomix_code-ref.md --quiet --include "docs/code_ref/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_docs.md --quiet --include "**/README.md,docs/**/*" --ignore "docs/code_ref*/**/*,docs/reference/deep-dives/**/*"

##################################################################################################
# CI/CD and Dependencies
##################################################################################################

# Run fast CI tests (for pull requests)
ci-test:
	@echo "🏭 Running CI tests (fast tests only)..."
	@cd backend && python -m pytest tests/ -v --cov=app --cov-report=xml
	@cd frontend && python -m pytest tests/ -v --cov=app --cov-report=xml
	@echo "🔍 Running code quality checks..."
	@cd backend && python -m flake8 app/
	@cd frontend && python -m flake8 app/
	@echo "⚙️  Validating resilience configuration..."
	@python scripts/validate_resilience_config.py --validate-current --quiet
	@echo "✅ CI tests completed!"

# Run comprehensive CI tests (for releases)
ci-test-all:
	@echo "🏭 Running comprehensive CI tests (including slow tests)..."
	@cd backend && python -m pytest tests/ -v --cov=app --cov-report=xml -m "not manual" --run-slow
	@cd frontend && python -m pytest tests/ -v --cov=app --cov-report=xml
	@echo "🔍 Running code quality checks..."
	@cd backend && python -m flake8 app/
	@cd frontend && python -m flake8 app/
	@echo "⚙️  Running preset-related tests..."
	@$(MAKE) test-presets
	@echo "⚙️  Validating all presets..."
	@python scripts/validate_resilience_config.py --validate-preset simple --quiet
	@python scripts/validate_resilience_config.py --validate-preset development --quiet
	@python scripts/validate_resilience_config.py --validate-preset production --quiet
	@echo "✅ Comprehensive CI tests completed!"

# Generate dependency lock files
lock-deps: venv
	@echo "🔒 Generating backend dependency lock files..."
	@cd backend && $(PYTHON_CMD) -m piptools compile requirements.txt --output-file requirements.lock
	@cd backend && $(PYTHON_CMD) -m piptools compile requirements-dev.txt --output-file requirements-dev.lock
	@echo "ℹ️  Note: Frontend dependencies are managed via Docker"
	@echo "✅ Lock files generated!"

# Update and lock dependencies
update-deps: venv
	@echo "🔄 Updating backend dependencies..."
	@cd backend && $(PYTHON_CMD) -m piptools compile --upgrade requirements.txt --output-file requirements.lock
	@cd backend && $(PYTHON_CMD) -m piptools compile --upgrade requirements-dev.txt --output-file requirements-dev.lock
	@echo "ℹ️  Note: Frontend dependencies are managed via Docker"
	@echo "✅ Dependencies updated!"

##################################################################################################
# Resilience Configuration Management
##################################################################################################

# List available resilience configuration presets
list-presets:
	@echo "⚙️  Available resilience configuration presets:"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --list-presets

# Show details of a specific preset
show-preset:
	@if [ -z "$(PRESET)" ]; then \
		echo "❌ Usage: make show-preset PRESET=<preset_name>"; \
		echo "💡 Available presets: simple, development, production"; \
		exit 1; \
	fi
	@echo "⚙️  Showing details for preset: $(PRESET)"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --show-preset $(PRESET)

# Validate current resilience configuration
validate-config:
	@echo "⚙️  Validating current resilience configuration..."
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --validate-current

# Validate a specific preset configuration
validate-preset:
	@if [ -z "$(PRESET)" ]; then \
		echo "❌ Usage: make validate-preset PRESET=<preset_name>"; \
		echo "💡 Available presets: simple, development, production"; \
		exit 1; \
	fi
	@echo "⚙️  Validating preset: $(PRESET)"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --validate-preset $(PRESET)

# Get preset recommendation for environment
recommend-preset:
	@if [ -z "$(ENV)" ]; then \
		echo "❌ Usage: make recommend-preset ENV=<environment>"; \
		echo "💡 Example environments: development, staging, production"; \
		exit 1; \
	fi
	@echo "⚙️  Getting preset recommendation for environment: $(ENV)"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --recommend-preset $(ENV)

# Migrate legacy configuration to presets
migrate-config:
	@echo "⚙️  Analyzing legacy configuration and providing migration recommendations..."
	@$(PYTHON_CMD) scripts/migrate_resilience_config.py

# Run all preset-related tests
test-presets:
	@echo "🧪 Running preset-related tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/unit/test_resilience_presets.py tests/integration/test_preset_resilience_integration.py -v

# ========================================
# CACHE PRESET MANAGEMENT COMMANDS
# ========================================

# List available cache configuration presets
list-cache-presets:
	@echo "🗂️  Available cache configuration presets:"
	@cd backend && $(PYTHON_CMD) scripts/validate_cache_config.py --list-presets

# Show details of a specific cache preset
show-cache-preset:
	@if [ -z "$(PRESET)" ]; then \
		echo "❌ Usage: make show-cache-preset PRESET=<preset_name>"; \
		echo "💡 Available presets: disabled, simple, development, production, ai-development, ai-production"; \
		exit 1; \
	fi
	@echo "🗂️  Showing details for cache preset: $(PRESET)"
	@cd backend && $(PYTHON_CMD) scripts/validate_cache_config.py --show-preset $(PRESET)

# Validate current cache configuration
validate-cache-config:
	@echo "🗂️  Validating current cache configuration..."
	@cd backend && $(PYTHON_CMD) scripts/validate_cache_config.py --validate-current

# Validate a specific cache preset configuration
validate-cache-preset:
	@if [ -z "$(PRESET)" ]; then \
		echo "❌ Usage: make validate-cache-preset PRESET=<preset_name>"; \
		echo "💡 Available presets: disabled, simple, development, production, ai-development, ai-production"; \
		exit 1; \
	fi
	@echo "🗂️  Validating cache preset: $(PRESET)"
	@cd backend && $(PYTHON_CMD) scripts/validate_cache_config.py --validate-preset $(PRESET)

# Get cache preset recommendation for environment
recommend-cache-preset:
	@if [ -z "$(ENV)" ]; then \
		echo "❌ Usage: make recommend-cache-preset ENV=<environment>"; \
		echo "💡 Example environments: development, staging, production, ai-development"; \
		exit 1; \
	fi
	@echo "🗂️  Getting cache preset recommendation for environment: $(ENV)"
	@cd backend && $(PYTHON_CMD) scripts/validate_cache_config.py --recommend-preset $(ENV)

# Migrate legacy cache configuration to presets
migrate-cache-config:
	@echo "🗂️  Analyzing legacy cache configuration and providing migration recommendations..."
	@cd backend && $(PYTHON_CMD) scripts/migrate_cache_config.py --analyze
