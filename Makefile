.PHONY: lint format check install-dev test

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Run linting checks
lint:
	ruff check .

# Fix linting issues
lint-fix:
	ruff check . --fix

# Format code
format:
	ruff format .

# Check formatting without making changes
format-check:
	ruff format . --check

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=custom_components.sabiana_energy_smart --cov-report=term-missing

# Run all checks
check: lint format-check test

# Run all fixes
fix: lint-fix format

# Run pre-commit hooks
pre-commit:
	pre-commit run --all-files