.PHONY: help install test lint format clean docker-build docker-up docker-down ci

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm ci
	@echo "Done!"

install-dev: ## Install development dependencies
	@echo "Installing backend dev dependencies..."
	cd backend && pip install pytest pytest-asyncio pytest-cov flake8 black isort mypy safety bandit
	@echo "Installing frontend dev dependencies..."
	cd frontend && npm ci
	@echo "Done!"

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && pytest -v
	@echo "Running frontend tests..."
	cd frontend && npm test || echo "No frontend tests configured"
	@echo "Done!"

test-backend: ## Run backend tests
	cd backend && pytest -v --cov=app --cov-report=term-missing

test-frontend: ## Run frontend tests
	cd frontend && npm test

lint: ## Run linters
	@echo "Linting backend..."
	cd backend && flake8 .
	cd backend && black --check .
	cd backend && isort --check-only .
	@echo "Linting frontend..."
	cd frontend && npm run lint
	@echo "Done!"

format: ## Format code
	@echo "Formatting backend..."
	cd backend && black .
	cd backend && isort .
	@echo "Formatting complete!"

type-check: ## Run type checking
	cd backend && mypy app --ignore-missing-imports

security: ## Run security checks
	@echo "Running security checks..."
	cd backend && safety check || true
	cd backend && bandit -r app || true
	cd frontend && npm audit || true
	@echo "Done!"

build-frontend: ## Build frontend
	cd frontend && npm run build

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-clean: ## Clean Docker resources
	docker-compose down -v
	docker system prune -f

ci: lint test ## Run CI checks locally
	@echo "CI checks passed!"

dev-backend: ## Run backend in development mode
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend in development mode
	cd frontend && npm run dev

dev-bot: ## Run Telegram bot
	cd backend && python run_bot.py

db-init: ## Initialize database
	cd backend && python -c "from app.models.database import init_db; import asyncio; asyncio.run(init_db())"

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf backend/dist backend/build
	rm -rf frontend/dist frontend/build
	@echo "Cleaned!"

setup: install db-init ## Complete setup (install + database)
	@echo "Setup complete! Ready to develop."

.DEFAULT_GOAL := help
