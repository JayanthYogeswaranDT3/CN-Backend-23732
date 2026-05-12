SHELL := /bin/bash

.PHONY: help install run dev test lint format migrate revision

help:
	@echo "Targets:"
	@echo "  install   - install deps into current environment"
	@echo "  run       - run uvicorn (no reload)"
	@echo "  dev       - run uvicorn with reload"
	@echo "  test      - run tests"
	@echo "  lint      - run ruff lint"
	@echo "  format    - run ruff format"
	@echo "  migrate   - run alembic upgrade head (requires DB)"
	@echo "  revision  - create alembic revision (requires msg=...)"

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

run:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest -q

lint:
	ruff check .

format:
	ruff format .

migrate:
	alembic upgrade head

revision:
	@if [ -z "$(msg)" ]; then echo "Usage: make revision msg='add users table'"; exit 1; fi
	alembic revision --autogenerate -m "$(msg)"
