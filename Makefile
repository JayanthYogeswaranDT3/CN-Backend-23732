SHELL := /bin/bash

PROJECT_NAME := cn-backend
COMPOSE := docker compose
APP_SERVICE := api

.PHONY: help
help:
	@echo "Targets:"
	@echo "  make up            - Start services (api + db)"
	@echo "  make down          - Stop services"
	@echo "  make logs          - Tail api logs"
	@echo "  make ps            - Show running containers"
	@echo "  make format        - Autoformat via ruff"
	@echo "  make lint          - Lint via ruff"
	@echo "  make test          - Run tests"
	@echo "  make alembic-init  - Initialize alembic (first time only)"
	@echo "  make migrate       - Create a new migration (requires MSG=...)"
	@echo "  make upgrade       - Apply migrations"

.PHONY: up
up:
	$(COMPOSE) up --build -d

.PHONY: down
down:
	$(COMPOSE) down

.PHONY: logs
logs:
	$(COMPOSE) logs -f $(APP_SERVICE)

.PHONY: ps
ps:
	$(COMPOSE) ps

.PHONY: format
format:
	python -m ruff format .
	python -m ruff check . --fix

.PHONY: lint
lint:
	python -m ruff format . --check
	python -m ruff check .

.PHONY: test
test:
	pytest -q

# Alembic helpers (run inside container so it uses container env)
.PHONY: alembic-init
alembic-init:
	$(COMPOSE) exec -T $(APP_SERVICE) alembic init alembic

.PHONY: migrate
migrate:
	@if [ -z "$(MSG)" ]; then echo "MSG is required, e.g. make migrate MSG='create items'"; exit 1; fi
	$(COMPOSE) exec -T $(APP_SERVICE) alembic revision --autogenerate -m "$(MSG)"

.PHONY: upgrade
upgrade:
	$(COMPOSE) exec -T $(APP_SERVICE) alembic upgrade head
"
