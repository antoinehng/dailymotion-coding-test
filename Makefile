# Makefile for Development Tooling
#
# While Makefiles may not be the fanciest or most modern approach to defining dev tooling
# commands, they provide exceptional reliability and universal compatibility. Make is a
# standard tool available on virtually every Unix-like system, making it the most accessible
# choice for development workflows.
#
# This approach ensures that any engineer, regardless of their preferred tooling or level
# of familiarity with project-specific tools, can easily discover and execute essential
# development tasks. By standardizing on Make, we guarantee that the basics are covered
# for everyone - from CI/CD pipelines to new contributors setting up their environment.
#
# Key benefits:
# - Universal availability (Linux, macOS, Docker containers)
# - No additional dependencies or runtime requirements
# - Self-documenting via `make help`
# - Consistent behavior across different environments
# - Works seamlessly with any language or toolchain

.PHONY: help check check-lint format check-format check-imports check-types check-security check-all test install-dev imports lint types security all

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: #m# Install development dependencies
	brew install uv gitleaks
	uv sync --group dev

format: ## Format code with ruff
	uv run ruff check --select I,F --fix .
	uv run ruff format .

check: ## Run checks (usage: make check [imports|lint|format|types|security|all])
	@if [ -z "$(filter-out check,$(MAKECMDGOALS))" ]; then \
		echo "Usage: make check [imports|lint|format|types|security|all]"; \
		exit 1; \
	fi
	@$(MAKE) check-$(filter-out check,$(MAKECMDGOALS))

# Dummy targets to prevent Make from treating arguments as unknown targets
imports lint types security all:
	@:

check-format: # Check code formatting without making changes
	uv run ruff format --check

check-lint: # Run ruff linter
	uv run ruff check

check-imports: # Check import structure with import-linter
	uv run lint-imports

check-types: # Run type checker
	uv run pyright

check-security: # Check for security vulnerabilities in dependencies and secrets
	uv run python -m pip_audit
	gitleaks dir ./ --max-decode-depth=10 --no-banner --redact=6

check-all: 
	$(MAKE) check-format
	$(MAKE) check-lint
	$(MAKE) check-imports
	$(MAKE) check-types
	$(MAKE) check-security

test: # Run tests with coverage report
	uv run coverage run -m pytest
	uv run coverage report --skip-covered --sort=cover --fail-under=80


start: # Start the dev server. Do not use in production!
	uv run granian --interface asgi src.http.app:app --host 0.0.0.0 --port 8000 --reload --loop uvloop --log-level debug
