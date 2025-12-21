.PHONY: help venv install install-dev test lint format typecheck coverage run-api run-ui clean all

# Default target
help:
	@echo "Google Photos Sync - Development Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  help         - Show this help message"
	@echo "  venv         - Create virtual environment using uv"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install production + development dependencies"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run ruff linter"
	@echo "  format       - Format code with ruff"
	@echo "  typecheck    - Run mypy type checker"
	@echo "  coverage     - Generate coverage report"
	@echo "  run-api      - Start Flask API server"
	@echo "  run-ui       - Start Streamlit UI"
	@echo "  clean        - Remove generated files and virtual environment"
	@echo "  all          - Create venv, install deps, lint, format, typecheck, test"

# Python and virtual environment paths
PYTHON := python3
VENV_DIR := .venv
VENV_BIN := $(VENV_DIR)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip
VENV_UV := $(VENV_BIN)/uv

# Check if running in virtual environment
check-venv:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠️  Warning: Not running in virtual environment!"; \
		echo "Please activate venv first:"; \
		echo "  source .venv/bin/activate  # Linux/macOS"; \
		echo "  .venv\\Scripts\\Activate.ps1  # Windows PowerShell"; \
		exit 1; \
	fi

# Create virtual environment using uv
venv:
	@echo "Creating virtual environment with uv..."
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment already exists at $(VENV_DIR)"; \
	else \
		uv venv $(VENV_DIR); \
		echo "✓ Virtual environment created successfully!"; \
		echo ""; \
		echo "Activate it with:"; \
		echo "  source .venv/bin/activate  # Linux/macOS"; \
		echo "  .venv\\Scripts\\Activate.ps1  # Windows PowerShell"; \
	fi

# Install production dependencies
install: check-venv
	@echo "Installing production dependencies with uv..."
	uv pip install -r requirements.txt
	@echo "✓ Production dependencies installed successfully!"

# Install production + development dependencies
install-dev: check-venv
	@echo "Installing production + development dependencies with uv..."
	uv pip install -r requirements.txt -r requirements-dev.txt
	@echo "✓ All dependencies installed successfully!"

# Run tests with coverage
test: check-venv
	@echo "Running tests with pytest..."
	pytest

# Run linter
lint: check-venv
	@echo "Running ruff linter..."
	ruff check .

# Format code
format: check-venv
	@echo "Formatting code with ruff..."
	ruff format .
	ruff check . --fix

# Run type checker
typecheck: check-venv
	@echo "Running mypy type checker..."
	mypy src/ --strict

# Generate coverage report
coverage: check-venv
	@echo "Generating coverage report..."
	pytest --cov=src --cov-report=term-missing --cov-report=html
	@echo "✓ Coverage report generated in htmlcov/"

# Run Flask API server
run-api: check-venv
	@echo "Starting Flask API server..."
	FLASK_APP=src/google_photos_sync/api/app.py $(VENV_PYTHON) -m flask run

# Run Streamlit UI
run-ui: check-venv
	@echo "Starting Streamlit UI..."
	$(VENV_PYTHON) -m streamlit run src/google_photos_sync/ui/app.py

# Clean generated files and virtual environment
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.coverage" -delete 2>/dev/null || true
	@echo "✓ Cleanup complete!"

# Complete setup: venv, install, lint, format, typecheck, test
all:
	@echo "Running complete setup..."
	@$(MAKE) venv
	@echo ""
	@echo "Please activate the virtual environment and run 'make install-dev' followed by 'make test'"
