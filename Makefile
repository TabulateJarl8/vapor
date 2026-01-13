.PHONY: test test-cov lint format build clean check-all

test:
	poetry run pytest . --numprocesses auto

test-cov:
	 poetry run pytest . --numprocesses auto --cov=vapor --cov-report=term-missing --cov-report=xml

format:
	poetry run ruff format .

lint:
	poetry run ruff check .

build:
	poetry build

clean:
	find . -type d -name "__pycache__" -exec rm -rfv "{}" +
	rm -rfv .mypy_cache .pytest_cache .ruff_cache dist htmlcov
	rm -fv .coverage coverage.xml

check-all: test-cov lint
	poetry run mypy .
	poetry run ruff format . --check
