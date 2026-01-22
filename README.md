# TODO Application

Event-driven TODO application built with an asynchronous Python stack.
This is a **training project in production style**, designed to explore modern backend technologies and architectural patterns while keeping the codebase clear and approachable.

The project is intended for a **junior+/middle backend portfolio**.

---

## Project goals

- Practice **FastAPI + Pydantic v2** in a realistic REST API
- Use **SQLAlchemy 2.0 (async)** with **Alembic migrations**
- Understand **event-driven architecture** with **Kafka**
- Build a system composed of **multiple services**
- Apply **Docker Compose** for local development
- Set up **CI quality gates** (linting, typing, tests, coverage)
- Keep the code **simple, explicit, and readable**

This repository prioritizes **clarity over cleverness**.

---

## Key features (planned)

- Async REST API (FastAPI)
- JWT-based authentication
- PostgreSQL as the single source of truth
- Kafka for domain events and background processing
- Microservices:
  - API service
  - Auth service
  - Scheduler service (cron-like logic)
  - Mailer service (event consumer)
- Docker Compose–based local environment
- pytest-based test suite with coverage
- GitHub Actions CI

---

## High-level architecture

The system follows an **event-driven architecture**:

- API services write state changes to PostgreSQL
- Significant state changes emit domain events to Kafka
- Background services react to events asynchronously
- Services do not call each other directly by default

Kafka provides **at-least-once delivery**, so consumers are expected to be idempotent.

More details:
- Architecture overview: `docs/architecture/`
- Event contracts: `docs/contracts/events/`
- REST contracts: `docs/contracts/rest/`

---

## Repository structure

```text
services/      # Backend services (API, auth, scheduler, mailer, shared)
infra/         # Docker, Kafka, Nginx configuration
docs/          # Architecture, contracts, ADRs, runbooks
tests/         # Test suites
.github/       # CI workflows, templates
```
## Documentation index

- Architecture: `docs/architecture/`
- REST & event contracts: `docs/contracts/` (REST planned)
- Tasks (step-by-step development): `docs/tasks/000-index.md`
- Architectural decisions: `docs/adr/`
- Operational notes: `docs/runbooks/`
- Project roadmap: `ROADMAP.md`
- Project specification: `TASK.md`
