.PHONY: help fmt fmt-check lint check test install dev-install type-check clean all venv activate

PYTHON := python3
SRC_DIR := tfe
TEST_DIR := tests
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

help:
	@echo "Available targets:"
	@echo "  venv             Create virtual environment"
	@echo "  activate         Show command to activate virtual environment"
	@echo "  install          Install package dependencies"
	@echo "  dev-install      Install package and development dependencies"
	@echo "  fmt              Format code"
	@echo "  fmt-check        Check code formatting"
	@echo "  lint             Run linting"
	@echo "  check            Run format check + lint + type check"
	@echo "  type-check       Run type checking"
	@echo "  test             Run unit tests"
	@echo "  clean            Clean build artifacts and cache"
	@echo "  all              Run clean + dev-install + fmt + lint + test"

$(VENV)/bin/activate: pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip

venv: $(VENV)/bin/activate

activate:
	@echo "To activate the virtual environment, run:"
	@echo "source $(VENV)/bin/activate"

install: venv
	$(VENV_PIP) install -e .

dev-install: venv
	$(VENV_PIP) install -e ".[dev]"

fmt:
	$(VENV_PYTHON) -m ruff format .
	$(VENV_PYTHON) -m ruff check --fix .

fmt-check:
	$(VENV_PYTHON) -m ruff format --check .
	$(VENV_PYTHON) -m ruff check .

lint:
	$(VENV_PYTHON) -m ruff check .
	$(VENV_PYTHON) -m mypy $(SRC_DIR)

check:
	$(VENV_PYTHON) -m ruff format --check .
	$(VENV_PYTHON) -m ruff check .
	$(VENV_PYTHON) -m mypy $(SRC_DIR)

type-check:
	$(VENV_PYTHON) -m mypy $(SRC_DIR)

test:
	$(VENV_PYTHON) -m pytest -v

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf build/ dist/ $(VENV)

all: clean dev-install fmt lint test
