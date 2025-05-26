.PHONY: help build up down logs clean dev prod test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs for all services
	docker-compose logs -f

clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

dev: ## Start development environment
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

prod: ## Start production environment
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

test: ## Run tests
	docker-compose exec backend python -m pytest tests/
	docker-compose exec frontend python -m pytest tests/

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

redis-logs: ## Show Redis logs
	docker-compose logs -f redis

nginx-logs: ## Show Nginx logs
	docker-compose logs -f nginx

status: ## Show status of all services
	docker-compose ps

health: ## Check health of all services
	@echo "Checking service health..."
	@docker-compose exec backend curl -f http://localhost:8000/health || echo "Backend unhealthy"
	@docker-compose exec frontend curl -f http://localhost:8501/_stcore/health || echo "Frontend unhealthy"
	@docker-compose exec redis redis-cli ping || echo "Redis unhealthy"

setup: ## Initial project setup
	@echo "🚀 Setting up FastAPI Streamlit LLM Starter..."
	@chmod +x scripts/*.sh 2>/dev/null || true
	@./scripts/setup.sh 2>/dev/null || echo "Setup script not found, skipping..."

install: ## Install dependencies locally
	@echo "📦 Installing dependencies..."
	@cd backend && pip install -r requirements.txt
	@cd frontend && pip install -r requirements.txt

format: ## Format code
	@echo "🎨 Formatting code..."
	@docker-compose exec backend black app/ || true
	@docker-compose exec backend isort app/ || true

lint: ## Lint code
	@echo "🔍 Linting code..."
	@docker-compose exec backend flake8 app/ || true
	@docker-compose exec backend mypy app/ || true

stop: ## Stop all services
	docker-compose stop

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

backup: ## Backup Redis data
	@echo "📦 Creating Redis backup..."
	@docker-compose exec redis redis-cli BGSAVE
	@docker cp ai-text-processor-redis:/data/dump.rdb ./backups/redis-$(shell date +%Y%m%d-%H%M%S).rdb

restore: ## Restore Redis data (usage: make restore BACKUP=filename)
	@echo "📦 Restoring Redis backup..."
	@docker cp ./backups/$(BACKUP) ai-text-processor-redis:/data/dump.rdb
	@docker-compose restart redis 