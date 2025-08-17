.PHONY: help up down build logs clean db-migrate seed backend-dev frontend-dev test eval

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

build: ## Build all services
	docker-compose build

logs: ## Show logs from all services
	docker-compose logs -f

clean: ## Remove all containers and volumes
	docker-compose down -v
	docker system prune -f

db-migrate: ## Run database migrations
	docker-compose exec backend python -m alembic upgrade head

db-reset: ## Reset database (drop and recreate)
	docker-compose exec backend python -m alembic downgrade base
	docker-compose exec backend python -m alembic upgrade head

seed: ## Seed database with initial data
	docker-compose exec backend python scripts/seed_data.py

backend-dev: ## Start backend in development mode
	docker-compose up -d db redis opa
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend-dev: ## Start frontend in development mode
	cd frontend && npm run dev

test: ## Run tests
	docker-compose exec backend python -m pytest
	cd frontend && npm test

test-backend: ## Run backend tests only
	docker-compose exec backend python -m pytest

test-frontend: ## Run frontend tests only
	cd frontend && npm test

lint: ## Run linting
	docker-compose exec backend python -m black . --check
	docker-compose exec backend python -m flake8 .
	cd frontend && npm run lint

format: ## Format code
	docker-compose exec backend python -m black .
	cd frontend && npm run format

eval: ## Run offline evaluations
	docker-compose exec backend python scripts/run_evaluations.py

policy-test: ## Test OPA policies
	docker-compose exec opa opa test /policies

policy-deploy: ## Deploy policies to OPA
	docker-compose exec opa opa eval --data /policies --input /policies/test-data.json data.governance

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-db: ## Show database logs
	docker-compose logs -f db

status: ## Show service status
	docker-compose ps

shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

shell-db: ## Open shell in database container
	docker-compose exec db psql -U postgres -d ai_governance

# Development shortcuts
dev: up db-migrate seed ## Full development setup
	@echo "Development environment ready!"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend API: http://localhost:8000/docs"
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Jaeger: http://localhost:16686"
	@echo "Prometheus: http://localhost:9090"
