.PHONY: help vet fmt lint test install dev-install type-check clean all

PYTHON := python3
PIPENV := pipenv
SRC_DIR := src
TEST_DIR := tests

help:
	@echo "Available targets:"
	@echo "  install          Install package dependencies"
	@echo "  dev-install      Install package and development dependencies"
	@echo "  fmt              Format code with ruff"
	@echo "  lint             Run linting (ruff + mypy)"
	@echo "  type-check       Run type checking with mypy"
	@echo "  test             Run unit tests"
	@echo "  clean            Clean build artifacts and cache"
	@echo "  all              Run clean + dev-install + fmt + lint + test"

install:
	$(PIPENV) install -e .

dev-install:
	$(PIPENV) install -e ".[dev]"

fmt:
	$(PIPENV) run ruff format .
	$(PIPENV) run ruff check --fix .

lint:
	$(PIPENV) run ruff check .
	$(PIPENV) run mypy $(SRC_DIR)

type-check:
	$(PIPENV) run mypy $(SRC_DIR)

test:
	$(PIPENV) run pytest

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf build/ dist/

all: clean dev-install fmt lint test
