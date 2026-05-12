SHELL := /bin/bash

.PHONY: help venv install run dev test lint format up down logs migrate revision dbshell

help:
	@echo "Targets:"
	@echo "  install   - install deps into current environment"
	@echo "  run       - run uvicorn (no reload)"
	@echo "  dev       - run uvicorn with reload"
	@echo "  test      - run tests"
	@echo "  lint      - run ruff lint"
	@echo "  format    - run ruff format"
	@echo "  up/down   - docker compose up/down"
	@echo "  logs      - docker compose logs -f"
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

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f

migrate:
	alembic upgrade head

revision:
	@if [ -z "$(msg)" ]; then echo "Usage: make revision msg='add users table'"; exit 1; fi
	alembic revision --autogenerate -m "$(msg)"
