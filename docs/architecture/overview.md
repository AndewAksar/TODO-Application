# Architecture Overview

## Status: Current

This document describes the implemented runtime architecture. Future evolution
is explicitly separated below.

## Current backend

The backend is one deployable FastAPI service, `services/api_gateway`:

```text
services/api_gateway
├── app/auth             JWT authentication and current-user resolution
├── app/tasks            task schemas, routes, and business rules
├── app/repositories     SQLAlchemy data access
├── app/models.py        User, Task, and ProcessedEvent ORM mappings
├── app/db.py            async engine and session factory
└── migrations           Alembic environment and revisions
```

Auth and tasks are application modules, not separate runtime services. FastAPI
registers both routers in the same application. Nginx serves the static
placeholder and proxies `/auth`, `/tasks`, health, OpenAPI, and Swagger traffic
to that application.

```mermaid
  CLIENT[Client / Swagger] --> NGINX[Nginx]
  NGINX --> API[api_gateway: FastAPI]
  API --> AUTH[auth module]
  API --> TASKS[tasks module]
  AUTH --> REPOS[repositories]
  TASKS --> REPOS
  REPOS --> DB[(PostgreSQL)]
```

## Current request boundaries

- Routes own HTTP validation, dependency injection, status codes, and error mapping.
- Services own business rules and write transaction boundaries.
- Repositories own owner-scoped SQLAlchemy operations but do not commit.
- `get_current_user` decodes the JWT and revalidates the user in PostgreSQL.
- Task routes pass only `current_user.id` into the task service.

PostgreSQL is the current persistent source of truth. Database access uses an
async SQLAlchemy engine and asyncpg; schema evolution uses Alembic.

## Current supporting containers

Docker Compose includes PostgreSQL, Kafka/Zookeeper, API, scheduler and mailer
images, Nginx, and the `api-tooling` profile. Only the API/PostgreSQL behavior
described above is current product behavior. Scheduler and mailer entry points
are placeholders, and the presence of Kafka infrastructure does not make task
CRUD event-driven.

## Planned evolution

Future roadmap work may introduce Kafka producers/consumers, an outbox,
operational scheduler and mailer workflows, background workers, and other
independently deployable components. Those are target-state ideas, not current
runtime claims. Backend decomposition should occur only for a concrete
architectural or operational reason.
