.PHONY: help setup dev prod test clean logs shell

# Default target
help:
	@echo "FastAPI Streamlit LLM Starter - Available Commands:"
	@echo ""
	@echo "  setup     - Initial project setup"
	@echo "  dev       - Start development environment"
	@echo "  prod      - Start production environment"
	@echo "  test      - Run tests"
	@echo "  clean     - Clean up containers and volumes"
	@echo "  logs      - Show application logs"
	@echo "  shell     - Open shell in backend container"
	@echo "  help      - Show this help message"

# Initial setup
setup:
	@echo "🚀 Setting up FastAPI Streamlit LLM Starter..."
	@chmod +x scripts/*.sh
	@./scripts/setup.sh

# Development environment
dev:
	@echo "🔧 Starting development environment..."
	@docker-compose -f docker-compose.yml up --build

# Production environment
prod:
	@echo "🚀 Starting production environment..."
	@docker-compose -f docker-compose.yml up -d --build

# Run tests
test:
	@echo "🧪 Running tests..."
	@docker-compose exec backend python -m pytest tests/ -v
	@docker-compose exec frontend python -m pytest tests/ -v

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	@docker-compose down -v
	@docker system prune -f

# Show logs
logs:
	@docker-compose logs -f

# Backend logs only
logs-backend:
	@docker-compose logs -f backend

# Frontend logs only
logs-frontend:
	@docker-compose logs -f frontend

# Open shell in backend container
shell:
	@docker-compose exec backend /bin/bash

# Install dependencies locally
install:
	@echo "📦 Installing dependencies..."
	@cd backend && pip install -r requirements.txt
	@cd frontend && pip install -r requirements.txt

# Format code
format:
	@echo "🎨 Formatting code..."
	@docker-compose exec backend black app/
	@docker-compose exec backend isort app/

# Lint code
lint:
	@echo "🔍 Linting code..."
	@docker-compose exec backend flake8 app/
	@docker-compose exec backend mypy app/

# Build images
build:
	@echo "🏗️ Building Docker images..."
	@docker-compose build

# Stop services
stop:
	@docker-compose stop

# Restart services
restart:
	@docker-compose restart

# Show status
status:
	@docker-compose ps 