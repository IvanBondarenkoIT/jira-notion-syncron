.PHONY: help install install-dev setup test lint format clean docker-build docker-up docker-down pre-commit

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
DOCKER_COMPOSE := docker-compose

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

setup: install-dev ## Initial project setup
	@echo "$(BLUE)Setting up project...$(NC)"
	pre-commit install
	@if not exist ".env" copy "config\.env.template" ".env"
	@echo "$(GREEN)✓ Project setup complete$(NC)"
	@echo "$(YELLOW)⚠ Don't forget to fill in .env file with your credentials$(NC)"

venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv venv
	@echo "$(GREEN)✓ Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate it with: venv\Scripts\activate (Windows) or source venv/bin/activate (Unix)$(NC)"

test: ## Run tests with coverage
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-unit: ## Run only unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTEST) tests/unit/ -v -m unit

test-integration: ## Run only integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTEST) tests/integration/ -v -m integration

lint: ## Run all linters
	@echo "$(BLUE)Running linters...$(NC)"
	@echo "$(YELLOW)→ Running flake8...$(NC)"
	flake8 src/ tests/
	@echo "$(YELLOW)→ Running pylint...$(NC)"
	pylint src/
	@echo "$(YELLOW)→ Running mypy...$(NC)"
	mypy src/
	@echo "$(GREEN)✓ All linters passed$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black src/ tests/
	isort src/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting without modifying
	@echo "$(BLUE)Checking code formatting...$(NC)"
	black --check src/ tests/
	isort --check-only src/ tests/

clean: ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	@if exist "htmlcov" rmdir /s /q htmlcov
	@if exist ".coverage" del .coverage
	@if exist ".pytest_cache" rmdir /s /q .pytest_cache
	@if exist ".mypy_cache" rmdir /s /q .mypy_cache
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@for /d /r . %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Docker containers started$(NC)"

docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Docker containers stopped$(NC)"

docker-logs: ## View Docker logs
	$(DOCKER_COMPOSE) logs -f

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"

sync: ## Run synchronization
	@echo "$(BLUE)Starting synchronization...$(NC)"
	$(PYTHON) -m src.presentation.cli.main sync

sync-dry-run: ## Run synchronization in dry-run mode
	@echo "$(BLUE)Starting dry-run synchronization...$(NC)"
	$(PYTHON) -m src.presentation.cli.main sync --dry-run

security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	bandit -r src/
	safety check
	@echo "$(GREEN)✓ Security checks passed$(NC)"

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	cd docs && make html
	@echo "$(GREEN)✓ Documentation generated$(NC)"

init-data: ## Initialize data directories with .gitkeep
	@echo "$(BLUE)Initializing data directories...$(NC)"
	@type nul > data\raw\.gitkeep
	@type nul > data\processed\.gitkeep
	@type nul > data\archive\.gitkeep
	@echo "$(GREEN)✓ Data directories initialized$(NC)"

