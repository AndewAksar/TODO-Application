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
API_TOOLING_SVC := api-tooling
TOOL := $(COMPOSE) --profile test run --rm $(API_TOOLING_SVC)
PY := python
PYTEST := $(PY) -m pytest
SCHEDULER_SVC := scheduler
RUFF := ruff
MYPY := mypy
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
	@echo "  Code Quality (runs inside docker test/tooling container):"
	@echo "    make lint            Run ruff check"
	@echo "    make format          Run ruff format"
	@echo "    make typecheck       Run mypy (if configured)"
	@echo "    make test            Run pytest"
	@echo ""
	@echo "  Local (runs in your .venv on host):"
	@echo "    make test-local      Run pytest locally (requires DATABASE_URL)"
	@echo "    make lint-local      Run ruff locally"
	@echo "    make format-local    Run ruff format locally"
	@echo "    make typecheck-local Run mypy locally"
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

# --- Quality (runs inside docker test/tooling container)
.PHONY: lint
lint:
	$(TOOL) ruff check .

.PHONY: format
format:
	$(TOOL) ruff format .

.PHONY: typecheck
typecheck:
	$(TOOL) mypy .

.PHONY: lint-local format-local typecheck-local
lint-local:
	@echo "Running LOCAL ruff (host venv)"
	$(RUFF) check .

format-local:
	@echo "Running LOCAL format (host venv)"
	$(RUFF) format .

typecheck-local:
	@echo "Running LOCAL mypy (host venv)"
	$(MYPY) .

.PHONY: test test-unit test-integration test-contract test-flaky
test:
	$(TOOL) $(PYTEST) -m "not flaky"

test-unit:
	$(TOOL) $(PYTEST) -m "unit and not flaky"

test-integration:
	$(TOOL) $(PYTEST) -m "integration and not flaky"

test-contract:
	$(TOOL) $(PYTEST) -m "contract and not flaky"

test-flaky:
	$(TOOL) $(PYTEST) -m "flaky"

# --- Local helpers
.PHONY: check-local-env
check-local-env:
	@if [ -z "$$DATABASE_URL" ]; then \
		echo ""; \
		echo "ERROR: DATABASE_URL is required for local tests."; \
		echo ""; \
		echo "Example:"; \
		echo "  DATABASE_URL='postgresql+asyncpg://x:x@localhost:5432/x' make test-local"; \
		echo ""; \
		exit 1; \
	fi

.PHONY: test-local test-local-unit test-local-integration test-local-contract
test-local: check-local-env
	@echo "Running LOCAL tests (host venv)"
	$(PYTEST) -m "not flaky"

test-local-unit: check-local-env
	$(PYTEST) -m "unit and not flaky"

test-local-integration: check-local-env
	$(PYTEST) -m "integration and not flaky"

test-local-contract: check-local-env
	$(PYTEST) -m "contract and not flaky"

.PHONY: check-local
check-local: lint-local typecheck-local test-local

.PHONY: test-docker
test-docker:
	$(TOOL) $(PYTEST) -m "not flaky"

# --- DB helpers
.PHONY: db-shell
db-shell:
	$(COMPOSE) exec $(DB_SVC) psql -U $$POSTGRES_USER -d $$POSTGRES_DB

# --- Alembic (inside tooling container)
.PHONY: migrate
migrate:
	$(TOOL) alembic upgrade head

# Example:
#   make makemigration M="create users table"
.PHONY: makemigration
makemigration:
	@if [ -z "$(M)" ]; then echo "ERROR: Provide message: make makemigration M=\"your message\""; exit 1; fi
	$(TOOL) alembic revision -m "$(M)"
