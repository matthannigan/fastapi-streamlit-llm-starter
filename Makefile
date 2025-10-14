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
#   - Python 3.12+ (Python 3.13 recommended) for backend development
#   - Docker and Docker Compose for containerized development
#   - Node.js for repomix documentation generation (optional)
##################################################################################################

# Declare all targets as phony to avoid conflicts with files
.PHONY: help install run test lint format clean docker dev docs \
        venv install-frontend install-frontend-local run-backend \
        test-local test-backend test-backend-api test-backend-core test-backend-infrastructure \
        test-backend-integration test-backend-performance test-backend-services test-backend-schemas \
        test-backend-slow test-backend-all test-backend-manual test-frontend test-integration \
        test-no-cryptography test-cryptography-unavailable \
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
        list-resil-presets show-resil-preset validate-resil-config validate-resil-preset recommend-resil-preset test-resil-presets \
        list-cache-presets show-cache-preset validate-cache-config validate-cache-preset recommend-cache-preset \
        poetry-maintenance poetry-security-scan poetry-update poetry-validate poetry-export poetry-install poetry-info poetry-dev install-backend-poetry

##################################################################################################
# Configuration and Environment Detection
##################################################################################################

# Selectively load variables from .env if present
ifneq (,$(wildcard .env))
    BACKEND_PORT  ?= $(shell grep -E '^[[:space:]]*BACKEND_PORT[[:space:]]*=' .env | tail -n1 | sed -E 's/^[[:space:]]*BACKEND_PORT[[:space:]]*=[[:space:]]*//')
    FRONTEND_PORT ?= $(shell grep -E '^[[:space:]]*FRONTEND_PORT[[:space:]]*=' .env | tail -n1 | sed -E 's/^[[:space:]]*FRONTEND_PORT[[:space:]]*=[[:space:]]*//')
    REDIS_PORT    ?= $(shell grep -E '^[[:space:]]*REDIS_PORT[[:space:]]*=' .env | tail -n1 | sed -E 's/^[[:space:]]*REDIS_PORT[[:space:]]*=[[:space:]]*//')
    REDIS_TLS_PORT    ?= $(shell grep -E '^[[:space:]]*REDIS_TLS_PORT[[:space:]]*=' .env | tail -n1 | sed -E 's/^[[:space:]]*REDIS_TLS_PORT[[:space:]]*=[[:space:]]*//')
    REPOMIX_CMD   ?= $(shell grep -E '^[[:space:]]*REPOMIX_CMD[[:space:]]*=' .env | tail -n1 | sed -E 's/^[[:space:]]*REPOMIX_CMD[[:space:]]*=[[:space:]]*//')
    export BACKEND_PORT FRONTEND_PORT REDIS_PORT REDIS_TLS_PORT REPOMIX_CMD
endif

# Set sensible defaults when not provided
BACKEND_PORT  ?= 8000
FRONTEND_PORT ?= 8501
REDIS_PORT    ?= 6379
REDIS_TLS_PORT    ?= 6380
REPOMIX_CMD   ?= npx repomix

# Also default when value exists but is empty
ifeq ($(strip $(BACKEND_PORT))),)
BACKEND_PORT := 8000
endif
ifeq ($(strip $(FRONTEND_PORT))),)
FRONTEND_PORT := 8501
endif
ifeq ($(strip $(REDIS_PORT))),)
REDIS_PORT := 6379
endif
ifeq ($(strip $(REDIS_TLS_PORT))),)
REDIS_TLS_PORT := 6380
endif
ifeq ($(strip $(REPOMIX_CMD))),)
REPOMIX_CMD := npx repomix
endif

# Python executable detection - prefer python3, fallback to python
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)
POETRY := $(shell command -v poetry 2> /dev/null)
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
HAS_POETRY := $(shell command -v poetry > /dev/null 2>&1 && echo "1" || echo "0")

# Select appropriate Python command based on current environment
ifeq ($(IN_DOCKER),1)
    PYTHON_CMD := python
else ifeq ($(IN_VENV),1)
    PYTHON_CMD := python
else
    PYTHON_CMD := $(VENV_PYTHON)
endif

# API base URL for documentation
API_BASE_URL := http://localhost:$(BACKEND_PORT)
export API_BASE_URL

# Example target to show the variables are loaded
show-env-vars:
	@echo "Project Name is: $(COMPOSE_PROJECT_NAME)"
	@echo "Git Branch is: $(GIT_BRANCH)"
	@echo "Virtual Env Status is: $(IN_VENV)"
	@echo "Docker Env Status is: $(IN_DOCKER)"
	@echo "Has Poetry is: $(HAS_POETRY)"
	@echo "Poetry Command is: $(POETRY)"
	@echo "Venv Directory is: $(VENV_DIR)"
	@echo "Venv Python Executable is: $(VENV_PYTHON)"
	@echo "Venv Pip Executable is: $(VENV_PIP)"
	@echo "Python Command is: $(PYTHON_CMD)"
	@echo "Backend Port is: $(BACKEND_PORT)"
	@echo "Frontend Port is: $(FRONTEND_PORT)"
	@echo "Redis Port is: $(REDIS_PORT)"
	@echo "Redis TLS Port is: $(REDIS_TLS_PORT)"
	@echo "API Base URL is: $(API_BASE_URL)"
	@echo "Repomix Command is: $(REPOMIX_CMD)"
	@echo "---"
	@echo "The shell also sees BACKEND_PORT as: $$BACKEND_PORT etc"
		
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
	@echo "  venv                 Create Python virtual environment for backend (pip-tools mode)"
	@echo "  poetry-install       Install all dependencies using Poetry (recommended)"
	@echo "  install              Install backend dependencies (auto-detects Poetry/pip-tools)"
	@echo "  install-backend      Install backend dependencies (auto-detects Poetry/pip-tools)"
	@echo "  install-frontend     Install frontend dependencies via Docker"
	@echo "  install-frontend-local  Install frontend deps in current venv (local dev)"
	@echo ""
	@echo "🖥️  DEVELOPMENT SERVERS:"
	@echo "  run-backend          Start FastAPI server locally (http://localhost:8000)"
	@echo "  dev                  Start full development environment with hot reload"
	@echo "  dev-secure           Start development environment with secure Redis (TLS + encryption)"
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
	@echo "  test-backend-infra-cache-e2e-redis  Run Redis-enhanced E2E cache tests (requires Docker)"
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
	@echo "  test-no-cryptography Run integration tests without cryptography (Docker)"
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
	@echo "  list-resil-presets         List available resilience presets"
	@echo "  show-resil-preset          Show preset details (Usage: PRESET=simple)"
	@echo "  validate-resil-config      Validate current resilience configuration"
	@echo "  validate-resil-preset      Validate specific preset (Usage: PRESET=simple)"
	@echo "  recommend-resil-preset     Get preset recommendation (Usage: ENV=development)"
	@echo "  test-resil-presets         Run all preset-related tests"
	@echo ""
	@echo "🗂️  CACHE CONFIGURATION:"
	@echo "  list-cache-presets   List available cache presets"
	@echo "  show-cache-preset    Show cache preset details (Usage: PRESET=development)"
	@echo "  validate-cache-config Validate current cache configuration"
	@echo "  validate-cache-preset Validate specific cache preset (Usage: PRESET=production)"
	@echo "  recommend-cache-preset Get cache preset recommendation (Usage: ENV=staging)"
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
	@echo "  make test-backend-infra-cache-e2e-redis # Test cache with real Redis"
	@echo "  make show-resil-preset PRESET=production  # Show production preset"
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

# Install all dependencies using Poetry (recommended)
poetry-install:
	@if [ "$(HAS_POETRY)" != "1" ]; then \
		echo "❌ Error: Poetry not found. Please install Poetry first:"; \
		echo "   curl -sSL https://install.python-poetry.org | python3 -"; \
		exit 1; \
	fi
	@echo "📦 Installing dependencies using Poetry..."
	@echo "🔧 Installing shared library..."
	@cd shared && poetry install
	@echo "🔧 Installing backend dependencies..."
	@cd backend && poetry install --with dev,test
	@echo "🔧 Installing frontend dependencies..."
	@cd frontend && poetry install --with dev,test
	@echo "✅ All Poetry dependencies installed successfully!"
	@echo "💡 Next steps:"
	@echo "   - make run-backend    # Start backend server"
	@echo "   - make dev            # Start full development environment"

# Install backend dependencies (auto-detects Poetry/pip-tools)
install: venv docusaurus-install
	@echo "📦 Installing backend dependencies..."
	@cd backend && source ../$(VENV_DIR)/bin/activate && pip install -r requirements.lock -r requirements-dev.lock
	@echo "✅ Backend dependencies installed successfully!"
	@echo "✅ project venv activated via: source $(VENV_DIR)/bin/activate"
	@echo "💡 Next steps:"
	@echo "   - make run-backend    # Start backend server"
	@echo "   - make dev            # Start full development environment"

# Optional Poetry support for backend development (uses root .venv)
install-backend-poetry: venv
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "❌ Poetry not found. Install with: curl -sSL https://install.python-poetry.org | python3 -"; \
		exit 1; \
	fi
	@echo "🔧 Configuring Poetry to use root virtual environment..."
	@cd backend && poetry env use $(shell pwd)/$(VENV_DIR)/bin/python
	@echo "🔧 Installing backend dependencies with Poetry..."
	@cd backend && poetry install --with dev,test
	@echo "✅ Backend Poetry environment ready using root .venv!"

# Use Poetry for enhanced dependency management with unified workflow
poetry-dev:
	@echo "🎯 Setting up Poetry development environment..."
	@$(MAKE) install-backend-poetry
	@echo "💡 Poetry environment ready!"
	@echo ""
	@echo "📝 UNIFIED WORKFLOW:"
	@echo "   Adding dependencies:"
	@echo "     cd backend && poetry add pytest-mock         # Adds to pyproject.toml + poetry.lock"
	@echo "     cd backend && poetry export --without-hashes -f requirements.txt > requirements.txt"
	@echo "     make install                                 # Installs into root .venv for consistency"
	@echo ""
	@echo "   Development commands:"
	@echo "     source .venv/bin/activate                    # Single environment for all tools"
	@echo "     pytest backend/tests/                       # Run tests"
	@echo "     uvicorn app.main:app --reload               # Run server"

# Export Poetry dependencies to requirements files for pip workflow
poetry-export:
	@echo "📤 Exporting Poetry dependencies to requirements files..."
	@cd backend && poetry export --without-hashes -f requirements.txt -o requirements.txt
	@cd backend && poetry export --without-hashes --with dev -f requirements.txt -o requirements-dev.txt
	@cd backend && poetry export --without-hashes --only dev -f requirements.txt -o requirements-dev-only.txt
	@echo "✅ Dependencies exported! Run 'make install' to install into root .venv"

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
	@CACHE_PRESET=$$(grep -E '^[[:space:]]*CACHE_PRESET[[:space:]]*=' .env 2>/dev/null | tail -n1 | sed -E 's/^[[:space:]]*CACHE_PRESET[[:space:]]*=[[:space:]]*//'); \
	CACHE_PRESET=$${CACHE_PRESET:-development}; \
	echo "🚀 Starting development environment..."; \
	echo "📍 Services will be available at:"; \
	echo "   🌐 Frontend (Streamlit): http://localhost:$(FRONTEND_PORT)"; \
	echo "   🔌 Backend (FastAPI):    http://localhost:$(BACKEND_PORT)"; \
	if [ "$$CACHE_PRESET" != "disabled" ]; then \
		echo "   🗄️  Redis:               redis://localhost:$(REDIS_PORT)"; \
	else \
		echo "   💾 Cache:                Memory-only (Redis disabled)"; \
	fi; \
	echo ""; \
	echo "💡 File watching enabled - changes will trigger automatic reloads"; \
	echo "⏹️  Press Ctrl+C to stop all services"; \
	echo ""; \
	if [ "$$CACHE_PRESET" = "disabled" ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build --watch; \
	else \
		docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile with-cache up --build --watch; \
	fi

# Start development environment with secure Redis (TLS + encryption)
dev-secure:
	@CACHE_PRESET=$$(grep -E '^[[:space:]]*CACHE_PRESET[[:space:]]*=' .env.secure 2>/dev/null | tail -n1 | sed -E 's/^[[:space:]]*CACHE_PRESET[[:space:]]*=[[:space:]]*//'); \
	CACHE_PRESET=$${CACHE_PRESET:-development}; \
	echo "🔐 Starting secure development environment..."; \
	echo "📍 Services will be available at:"; \
	echo "   🌐 Frontend (Streamlit): http://localhost:$(FRONTEND_PORT)"; \
	echo "   🔌 Backend (FastAPI):    http://localhost:$(BACKEND_PORT)"; \
	if [ "$$CACHE_PRESET" != "disabled" ]; then \
		echo "   🗄️  Redis (TLS):         rediss://localhost:$(REDIS_TLS_PORT)"; \
	else \
		echo "   💾 Cache:                Memory-only (Redis disabled)"; \
	fi; \
	echo ""; \
	if [ "$$CACHE_PRESET" != "disabled" ]; then \
		echo "🔒 Security features enabled:"; \
		echo "   ✓ TLS encryption for Redis connections"; \
		echo "   ✓ Password authentication"; \
		echo "   ✓ Application-layer data encryption"; \
		echo ""; \
		echo "💡 Run './scripts/setup-secure-redis.sh' first if you haven't already"; \
	fi; \
	echo "⏹️  Press Ctrl+C to stop all services"; \
	echo ""; \
	if [ ! -f .env.secure ]; then \
		echo "❌ Error: .env.secure not found"; \
		echo "Run: ./scripts/setup-secure-redis.sh"; \
		exit 1; \
	fi; \
	if [ "$$CACHE_PRESET" = "disabled" ]; then \
		docker-compose -f docker-compose.secure.yml --env-file .env.secure up --build; \
	else \
		docker-compose -f docker-compose.secure.yml --env-file .env.secure --profile with-cache up --build; \
	fi

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

update-tests-progress:
	@echo "🧪 Updating tests progress..."
	@-cd backend && $(PYTHON_CMD) -m pytest tests/infrastructure/cache/ -n auto -q --json-report --json-report-file=tests/infrastructure/cache/failures.json
	@$(PYTHON_CMD) scripts/update_tests_progress_w_failures.py backend/tests/infrastructure/cache/ --failures backend/tests/infrastructure/cache/failures.json --output backend/tests/infrastructure/cache/PROGRESS.md


# Run all backend tests
test-backend:
	@-$(MAKE) test-backend-unit
	@-$(MAKE) test-backend-integration
	@-$(MAKE) test-backend-e2e

# Run backend unit tests
test-backend-unit:
	@echo "🧪 Running backend unit tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/unit/ --tb=short

test-backend-integration:
	@echo "🧪 Running backend integration tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/integration/ --tb=no --retries 3 --retry-delay 1

test-backend-e2e:
	@echo "🧪 Running backend E2E tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/e2e/ -m "e2e" -q --tb=no --retries 3 --retry-delay 1


# Run cache infrastructure tests
test-backend-cache:
	@-$(MAKE) test-backend-cache-unit
	@-$(MAKE) test-backend-cache-integration
	@-$(MAKE) test-backend-cache-e2e

test-backend-cache-unit:
	@echo "🧪 Running backend cache infrastructure unit tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/unit/cache/ -n auto -q --tb=no

test-backend-cache-integration:
	@echo "🧪 Running backend cache infrastructure integration tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/integration/cache/ -n 0 -q --tb=no --retries 3 --retry-delay 1

test-backend-cache-e2e:
	@echo "🧪 Running backend cache infrastructure E2E tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/e2e/cache/ -n 0 -m "e2e" -q --tb=no --retries 3 --retry-delay 1


# Run core environment tests
test-backend-environment:
	@$(MAKE) test-backend-environment-unit
	@$(MAKE) test-backend-environment-integration
#	@$(MAKE) test-backend-environment-e2e

test-backend-environment-unit:
	@echo "🧪 Running backend core environment unit tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/unit/environment/ -n auto -v --tb=no

test-backend-environment-integration:
	@echo "🧪 Running backend core environment integration tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/integration/environment/ -n 0 -v --tb=short --retries 1 --retry-delay 1


# Run auth infrastructure tests
test-backend-auth:
	@$(MAKE) test-backend-auth-unit
	@$(MAKE) test-backend-auth-integration
#	@$(MAKE) test-backend-auth-e2e

test-backend-auth-unit:
	@echo "🧪 Running backend auth infrastructure unit tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/unit/auth/ -n auto -v --tb=no

test-backend-auth-integration:
	@echo "🧪 Running backend auth infrastructure integration tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/integration/auth/ -n 0 -v --tb=short --retries 1 --retry-delay 1


# Run slow/comprehensive backend tests
test-backend-slow:
	@echo "🧪 Running slow backend tests (comprehensive)..."
	@echo "⏳ This may take several minutes..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/ -v -m "slow" --run-slow --timeout=60

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

# Run integration tests without cryptography library (Docker-based)
test-no-cryptography:
	@echo "🔒 Running integration tests without cryptography library..."
	@echo "⚠️  These tests verify graceful degradation when cryptography is unavailable"
	@echo ""
	@bash backend/tests/integration/docker/run-no-cryptography-tests.sh

# Alias for test-no-cryptography
test-cryptography-unavailable: test-no-cryptography

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

lint-recent:
	@echo "🔍 Running recent code quality checks on recently changed Python files..."
	@{ git diff --name-only ; git diff --name-only --staged ; git ls-files --other --exclude-standard ; } | sort | uniq | grep '\.py$' | xargs ruff check --fix
	@{ git diff --name-only ; git diff --name-only --staged ; git ls-files --other --exclude-standard ; } | sort | uniq | grep '\.py$' | xargs .venv/bin/python -m mypy --ignore-missing-imports

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
# args: FILE=<path/to/file.py>
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
	@cd frontend && $(PYTHON_CMD) -m black app/ tests/
	@cd frontend && $(PYTHON_CMD) -m isort app/ tests/
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
	@rm -f docs/code_ref/backend/index.md && rm -f docs/code_ref/backend/app/api/index.md && rm -f docs/code_ref/frontend/index.md && rm -f docs/code_ref/shared/index.md
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
	@$(MAKE) repomix-recent
	@$(MAKE) repomix-backend
	@$(MAKE) repomix-backend-contracts
	@$(MAKE) repomix-frontend  
	@$(MAKE) repomix-docs
	@echo "✅ All repository documentation generated in repomix-output/"

repomix-recent:
	@echo "📄 Generating recent repository documentation..."
	@mkdir -p repomix-output
	@{ git diff --name-only ; git diff --name-only --staged ; git ls-files --other --exclude-standard ; } | sort | uniq | $(REPOMIX_CMD) --stdin --quiet --output repomix-output/repomix_recent.md


# Generate backend main documentation
repomix-backend: repomix-backend-tests
	@echo "📄 Generating backend documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-ALL_U.md --quiet --include "backend/**/*,shared/**/*,.env.example*,docs/guides/application/BACKEND.md" --ignore "backend/contracts/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-app_U.md --quiet --include "backend/**/*,shared/**/*,.env.example*,docs/guides/application/BACKEND.md" --ignore "backend/contracts/**/*,backend/examples/**/*,backend/scripts/**/*,backend/tests/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-app_C.md --quiet --include "backend/**/*,shared/**/*,.env.example*,docs/guides/application/BACKEND.md" --ignore "backend/contracts/**/*,backend/examples/**/*,backend/scripts/**/*,backend/tests/**/*" --compress

# Generate backend tests documentation
repomix-backend-tests:
	@echo "📄 Generating backend tests documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-tests_U.md --quiet --include "backend/tests/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-tests_C.md --quiet --include "backend/tests/**/*" --compress

# Generate backend unit test fixtures documentation
repomix-backend-conftest:
	@echo "📄 Generating backend unit test fixtures documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-conftest_U.md --quiet --include "backend/tests/**/conftest.py"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-conftest_shared-unit_U.md --quiet --include "backend/tests/unit/*/conftest.py,backend/tests/unit/conftest.py"
#	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-conftest_resilience_U.md --quiet --include "backend/tests/unit/resilience/**/conftest.py,backend/tests/unit/conftest.py"
#	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-conftest_llm_security_U.md --quiet --include "backend/tests/unit/llm_security/**/conftest.py,backend/tests/unit/conftest.py"

# Generate backend contracts documentation 
repomix-backend-contracts: generate-contracts
	@echo "📄 Generating backend cache documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-contracts.md --quiet --no-file-summary --header-text "$$(cat backend/contracts/repomix-instructions.md)" --include "backend/contracts/**/*" --ignore "backend/contracts/repomix-instructions.md"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-contracts-cache.md --quiet --no-file-summary --header-text "$$(cat backend/contracts/repomix-instructions.md)" --include "backend/contracts/**/cache/**/*,backend/contracts/**/*cache*.*" --ignore "backend/contracts/repomix-instructions.md"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-contracts-resilience.md --quiet --no-file-summary --header-text "$$(cat backend/contracts/repomix-instructions.md)" --include "backend/contracts/**/resilience/**/*,backend/contracts/**/*resilience*.*" --ignore "backend/contracts/repomix-instructions.md"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-contracts-llm_security.md --quiet --no-file-summary --header-text "$$(cat backend/contracts/repomix-instructions.md)" --include "backend/contracts/**/security/llm/**/*,backend/contracts/**/*llm_security*.*" --ignore "backend/contracts/repomix-instructions.md"

# Generate backend cache documentation 
repomix-backend-cache: repomix-backend-cache-tests
	@echo "📄 Generating backend cache documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-cache_U.md --quiet --include "backend/**/cache/**/*,backend/**/*cache*.*,backend/**/*CACHE*.*,.env.example,docs/guides/application/BACKEND.md,docs/**/cache/**/*,docs/**/*cache*.*" --ignore "backend/contracts/**/*,docs/code_ref/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-cache_C.md --quiet --include "backend/**/cache/**/*,backend/**/*cache*.*,backend/**/*CACHE*.*,.env.example,docs/guides/application/BACKEND.md,docs/**/cache/**/*,docs/**/*cache*.*" --ignore "backend/contracts/**/*,docs/code_ref/**/*" --compress
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-contracts-cache.md --quiet --no-file-summary --header-text "$$(cat backend/contracts/repomix-instructions.md)" --include "backend/contracts/**/cache/**/*,backend/contracts/**/*cache*.*"

repomix-backend-cache-tests:
	@echo "📄 Generating backend tests cache documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-cache-tests_U.md --quiet --include "backend/tests/**/cache/**/*,backend/tests/**/*cache*.*"
#	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-cache-tests-e2e_U.md --quiet --include "backend/tests/infrastructure/cache/e2e/**/*,backend/tests/infrastructure/cache/conftest.py"

# Generate backend environment documentation 
repomix-backend-environment: repomix-backend-environment-tests
	@echo "📄 Generating backend environment documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-environment_U.md --quiet --include "backend/**/environment/**/*,backend/**/*environment*.*,backend/**/*environment*.*,.env.example,docs/guides/application/BACKEND.md,docs/**/environment/**/*,docs/**/*environment*.*" --ignore "backend/contracts/**/*,docs/code_ref/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-environment_C.md --quiet --include "backend/**/environment/**/*,backend/**/*environment*.*,backend/**/*environment*.*,.env.example,docs/guides/application/BACKEND.md,docs/**/environment/**/*,docs/**/*environment*.*" --ignore "backend/contracts/**/*,docs/code_ref/**/*" --compress
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-contracts-environment.md --quiet --no-file-summary --header-text "$$(cat backend/contracts/repomix-instructions.md)" --include "backend/contracts/**/environment/**/*,backend/contracts/**/*environment*.*"

repomix-backend-environment-tests:
	@echo "📄 Generating backend tests environment documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-environment-tests_U.md --quiet --include "backend/tests/**/environment/**/*,backend/tests/**/*environment*.*"
#	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-environment-tests-e2e_U.md --quiet --include "backend/tests/infrastructure/environment/e2e/**/*,backend/tests/infrastructure/environment/conftest.py"

# Generate backend security/auth documentation 
repomix-backend-security-auth: repomix-backend-security-auth-tests
	@echo "📄 Generating backend security/auth documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-security-auth_U.md --quiet --include "backend/**/security/**/*,backend/**/*security*.*,backend/**/*security*.*,.env.example,docs/guides/application/BACKEND.md,docs/**/security/**/*,docs/**/*security*.*,backend/**/auth/**/*,backend/**/*auth*.*,backend/**/*auth*.*,docs/**/auth/**/*,docs/**/*auth*.*,docs/**/SECURITY.md,docs/**/AUTHENTICATION.md" --ignore "backend/contracts/**/*,docs/code_ref/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-security-auth_C.md --quiet --include "backend/**/security/**/*,backend/**/*security*.*,backend/**/*security*.*,.env.example,docs/guides/application/BACKEND.md,docs/**/security/**/*,docs/**/*security*.*,backend/**/auth/**/*,backend/**/*auth*.*,backend/**/*auth*.*,docs/**/auth/**/*,docs/**/*auth*.*,docs/**/SECURITY.md,docs/**/AUTHENTICATION.md" --ignore "backend/contracts/**/*,docs/code_ref/**/*" --compress
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-contracts-security-auth.md --quiet --no-file-summary --header-text "$$(cat backend/contracts/repomix-instructions.md)" --include "backend/contracts/**/security/**/*,backend/contracts/**/*security*.*,backend/contracts/**/auth/**/*,backend/contracts/**/auth*.*"

repomix-backend-security-auth-tests:
	@echo "📄 Generating backend tests security/auth documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-security-auth-tests_U.md --quiet --include "backend/tests/**/security/**/*,backend/tests/**/*security*.*,backend/tests/**/auth/**/*,backend/tests/**/auth*.*"
#	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-security-auth-tests-e2e_U.md --quiet --include "backend/tests/infrastructure/security/e2e/**/*,backend/tests/infrastructure/security/conftest.py,backend/tests/infrastructure/auth/e2e/**/*,backend/tests/infrastructure/auth/conftest.py"

repomix-backend-resilience-tests:
	@echo "📄 Generating backend tests resilience documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-resilience-tests_U.md --quiet --include "backend/tests/unit/resilience/**/*,backend/tests/unit/conftest.py"
	
repomix-backend-security-llm-tests:
	@echo "📄 Generating backend tests llm_security documentation..."
	@mkdir -p repomix-output
	@$(REPOMIX_CMD) --output repomix-output/repomix_backend-security-llm-tests_U.md --quiet --include "backend/tests/unit/llm_security/**/*,backend/tests/unit/conftest.py"
	
# Generate frontend-only documentation
repomix-frontend: repomix-frontend-tests
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
	@$(REPOMIX_CMD) --output repomix-output/repomix_code-ref.md --quiet --include "docs/code_ref/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_docs.md --quiet --include "**/README.md,docs/**/*" --ignore "docs/code_ref*/**/*,docs/reference/deep-dives/**/*"
	@$(REPOMIX_CMD) --output repomix-output/repomix_docs-testing.md --quiet --include "docs/guides/testing/**/*"	

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
	@$(MAKE) test-resil-presets
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
list-resil-presets:
	@echo "⚙️  Available resilience configuration presets:"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --list-resil-presets

# Show details of a specific preset
# args: PRESET=<preset_name>
show-resil-preset:
	@if [ -z "$(PRESET)" ]; then \
		echo "❌ Usage: make show-resil-preset PRESET=<preset_name>"; \
		echo "💡 Available presets: simple, development, production"; \
		exit 1; \
	fi
	@echo "⚙️  Showing details for preset: $(PRESET)"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --show-resil-preset $(PRESET)

# Validate current resilience configuration
validate-resil-config:
	@echo "⚙️  Validating current resilience configuration..."
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --validate-current

# Validate a specific preset configuration
# args: PRESET=<preset_name>
validate-resil-preset:
	@if [ -z "$(PRESET)" ]; then \
		echo "❌ Usage: make validate-resil-preset PRESET=<preset_name>"; \
		echo "💡 Available presets: simple, development, production"; \
		exit 1; \
	fi
	@echo "⚙️  Validating preset: $(PRESET)"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --validate-preset $(PRESET)

# Get preset recommendation for environment
# args: ENV=<environment>
recommend-resil-preset:
	@if [ -z "$(ENV)" ]; then \
		echo "❌ Usage: make recommend-resil-preset ENV=<environment>"; \
		echo "💡 Example environments: development, staging, production"; \
		exit 1; \
	fi
	@echo "⚙️  Getting preset recommendation for environment: $(ENV)"
	@$(PYTHON_CMD) scripts/validate_resilience_config.py --recommend-preset $(ENV)

# Run all preset-related tests
test-resil-presets:
	@echo "🧪 Running preset-related tests..."
	@cd backend && $(PYTHON_CMD) -m pytest tests/unit/test_resilience_presets.py tests/integration/test_preset_resilience_integration.py -v

# ========================================
# CACHE PRESET MANAGEMENT COMMANDS
# ========================================

# List available cache configuration presets
list-cache-presets:
	@echo "🗂️  Available cache configuration presets:"
	@cd backend && $(PYTHON_CMD) scripts/validate_cache_config.py --list-resil-presets

# Show details of a specific cache preset
# args: PRESET=<preset_name>
show-cache-preset:
	@if [ -z "$(PRESET)" ]; then \
		echo "❌ Usage: make show-cache-preset PRESET=<preset_name>"; \
		echo "💡 Available presets: disabled, simple, development, production, ai-development, ai-production"; \
		exit 1; \
	fi
	@echo "🗂️  Showing details for cache preset: $(PRESET)"
	@cd backend && $(PYTHON_CMD) scripts/validate_cache_config.py --show-resil-preset $(PRESET)

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
# args: ENV=<environment>
recommend-cache-preset:
	@if [ -z "$(ENV)" ]; then \
		echo "❌ Usage: make recommend-cache-preset ENV=<environment>"; \
		echo "💡 Example environments: development, staging, production, ai-development"; \
		exit 1; \
	fi
	@echo "🗂️  Getting cache preset recommendation for environment: $(ENV)"
	@cd backend && $(PYTHON_CMD) scripts/validate_cache_config.py --recommend-preset $(ENV)


# ========================================
# POETRY MAINTENANCE COMMANDS
# ========================================

# Run comprehensive Poetry maintenance report
poetry-maintenance:
	@echo "🔧 Running comprehensive Poetry maintenance check..."
	@$(PYTHON_CMD) scripts/poetry_maintenance.py

# Run Poetry security scanning across all components
poetry-security-scan:
	@echo "🔒 Running Poetry security scan..."
	@$(PYTHON_CMD) scripts/poetry_maintenance.py security-scan

# Update all Poetry dependencies across components
poetry-update:
	@echo "📦 Updating all Poetry dependencies..."
	@$(PYTHON_CMD) scripts/poetry_maintenance.py update

# Validate Poetry cross-component compatibility
poetry-validate:
	@echo "🔗 Validating Poetry cross-component compatibility..."
	@$(PYTHON_CMD) scripts/poetry_maintenance.py validate



# Show Poetry dependency information
poetry-info:
	@echo "📋 Poetry Dependency Information:"
	@echo ""
	@echo "📦 Backend Dependencies (via Poetry):"
	@cd backend && poetry show --tree
	@echo ""
	@echo "🖥️  Frontend Dependencies:"
	@echo "   Frontend uses Docker-only approach (no Poetry environment)"
	@echo "   See frontend/Dockerfile for dependency management"
	@echo ""
	@echo "🔗 Shared Library Dependencies:"
	@echo "   Shared library has minimal pyproject.toml for pip compatibility"
	@echo "   Dependencies managed via backend Poetry environment"

