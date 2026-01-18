# Makefile for Event-Driven TODO (FastAPI + Kafka) project
# Usage:
#   make help
#   make up
#   make logs-api
#   make shell-api
#   make lint
#   make test
#
# Requirements:
#   - docker + docker compose
# Optional:
#   - local ruff/pytest if you add non-docker targets later

SHELL := /bin/sh

COMPOSE := docker compose
PROJECT_NAME := todo-kafka

# Services (must match docker-compose.yml service names)
API_SVC := api
SCHEDULER_SVC := scheduler
MAILER_SVC := mailer
FRONTEND_SVC := frontend
DB_SVC := postgres
KAFKA_SVC := kafka

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Available targets:"
	@echo ""
	@echo "  Bootstrap / Infra:"
	@echo "    make up              Start all services in background"
	@echo "    make down            Stop services and remove volumes"
	@echo "    make build           Build images"
	@echo "    make restart         Restart all services"
	@echo "    make ps              Show running containers"
	@echo "    make logs            Follow logs for all services"
	@echo ""
	@echo "  Logs (per service):"
	@echo "    make logs-api        Follow API logs"
	@echo "    make logs-scheduler  Follow Scheduler logs"
	@echo "    make logs-mailer     Follow Mailer logs"
	@echo "    make logs-kafka      Follow Kafka logs"
	@echo ""
	@echo "  Shell / Debug:"
	@echo "    make shell-api       Open shell in API container"
	@echo "    make shell-scheduler Open shell in Scheduler container"
	@echo "    make shell-mailer    Open shell in Mailer container"
	@echo ""
	@echo "  Code Quality (runs inside API container by default):"
	@echo "    make lint            Run ruff check"
	@echo "    make format          Run ruff format"
	@echo "    make typecheck       Run mypy (if configured)"
	@echo "    make test            Run pytest"
	@echo ""
	@echo "  Database / Migrations:"
	@echo "    make db-shell        Open psql shell"
	@echo "    make migrate         Apply Alembic migrations to head"
	@echo "    make makemigration M=\"msg\"  Create new Alembic revision"
	@echo ""
	@echo "Tips:"
	@echo "  - Ensure docker-compose service names match variables at top."
	@echo "  - If your API container uses a non-root user, keep /bin/sh."

.PHONY: up
up:
	$(COMPOSE) up -d

.PHONY: down
down:
	$(COMPOSE) down -v

.PHONY: build
build:
	$(COMPOSE) build

.PHONY: restart
restart:
	$(COMPOSE) restart

.PHONY: ps
ps:
	$(COMPOSE) ps

.PHONY: logs
logs:
	$(COMPOSE) logs -f --tail=200

.PHONY: logs-api
logs-api:
	$(COMPOSE) logs -f --tail=200 $(API_SVC)

.PHONY: logs-scheduler
logs-scheduler:
	$(COMPOSE) logs -f --tail=200 $(SCHEDULER_SVC)

.PHONY: logs-mailer
logs-mailer:
	$(COMPOSE) logs -f --tail=200 $(MAILER_SVC)

.PHONY: logs-kafka
logs-kafka:
	$(COMPOSE) logs -f --tail=200 $(KAFKA_SVC)

.PHONY: shell-api
shell-api:
	$(COMPOSE) exec $(API_SVC) /bin/sh

.PHONY: shell-scheduler
shell-scheduler:
	$(COMPOSE) exec $(SCHEDULER_SVC) /bin/sh

.PHONY: shell-mailer
shell-mailer:
	$(COMPOSE) exec $(MAILER_SVC) /bin/sh

# --- Quality (default inside API container)
.PHONY: lint
lint:
	$(COMPOSE) exec $(API_SVC) ruff check .

.PHONY: format
format:
	$(COMPOSE) exec $(API_SVC) ruff format .

.PHONY: typecheck
typecheck:
	$(COMPOSE) exec $(API_SVC) mypy .

.PHONY: test
test:
	$(COMPOSE) exec $(API_SVC) pytest -q

# --- DB helpers
.PHONY: db-shell
db-shell:
	$(COMPOSE) exec $(DB_SVC) psql -U $$POSTGRES_USER -d $$POSTGRES_DB

# --- Alembic (inside API container)
.PHONY: migrate
migrate:
	$(COMPOSE) exec $(API_SVC) alembic upgrade head

# Example:
#   make makemigration M="create users table"
.PHONY: makemigration
makemigration:
	@if [ -z "$(M)" ]; then echo "ERROR: Provide message: make makemigration M=\"your message\""; exit 1; fi
	$(COMPOSE) exec $(API_SVC) alembic revision -m "$(M)"
