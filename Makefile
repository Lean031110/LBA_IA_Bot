.PHONY: install test lint format clean backup run

# Variables
PYTHON = python3
PIP = pip3
PYTEST = pytest
FLAKE8 = flake8
BLACK = black
ISORT = isort

# Instalación
install:
	$(PIP) install -r requirements.txt

# Tests
test:
	$(PYTEST) tests/ -v

# Linting y formateo
lint:
	$(FLAKE8) .
	$(BLACK) . --check
	$(ISORT) . --check-only

format:
	$(BLACK) .
	$(ISORT) .

# Limpieza
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

# Backup
backup:
	@echo "Creating backup..."
	@mkdir -p data/backups
	@tar -czf "data/backups/backup_$(shell date +%Y%m%d_%H%M%S).tar.gz" \
		--exclude="*.pyc" \
		--exclude="__pycache__" \
		--exclude=".git" \
		--exclude="data/backups" \
		.

# Ejecución
run:
	$(PYTHON) main.py