.PHONY: test test-cov lint format build clean

test:
	poetry run pytest . --numprocesses auto

test-cov:
	 poetry run pytest . --numprocesses auto --cov=vapor --cov-report=term-missing --cov-report=xml

format:
	poetry run ruff format .

lint:
	poetry run ruff lint .

build:
	poetry build

clean:
	find . -type d -name "__pycache__" -exec rm -rfv "{}" +
	rm -rfv .mypy_cache .pytest_cache .ruff_cache .dist .htmlcov
	rm -v .coverage .coverage.xml
