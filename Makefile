.PHONY: lint format check install-dev

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

# Run all checks
check: lint format-check

# Run all fixes
fix: lint-fix format

# Run pre-commit hooks
pre-commit:
	pre-commit run --all-files