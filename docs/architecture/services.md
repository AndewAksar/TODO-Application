# Services and Responsibilities

## Status: Current

## Implemented runtime components

| Component | Path | Current responsibility |
|---|---|---|
| API gateway | `services/api_gateway` | One deployable FastAPI backend containing auth, task CRUD, repositories, models, DB access, and migrations |
| Auth module | `services/api_gateway/app/auth` | Register/login, JWT issuance, and authenticated-user dependency |
| Tasks module | `services/api_gateway/app/tasks` | Human-facing task schemas/routes and task business rules |
| Repositories | `services/api_gateway/app/repositories` | Async SQLAlchemy access for users and owner-scoped tasks |
| Nginx | `infra/nginx/nginx.conf` | Static placeholder serving and reverse proxy for current API routes |
| PostgreSQL | Compose service `postgres` | Persistent source of truth |
| Tooling | Compose service `api-tooling` | Tests, lint, typecheck, and Alembic operations; not a runtime service |
| Test PostgreSQL | Compose service `postgres-test` | Isolated `todo_test` database for integration tests |

The API service owns the current `users`, `tasks`, and `processed_events` ORM
mappings and the Alembic migration chain. The presence of `processed_events`
does not by itself mean that an event consumer is operational.

## Present but not operational product workflows

| Component | Path | Current status |
|---|---|---|
| Scheduler | `services/scheduler_service` | Container/service skeleton; planned daily-digest behavior is not implemented |
| Mailer | `services/mailer_service` | Container/service skeleton; Kafka consumption and email delivery are not implemented |
| Kafka/Zookeeper | `docker-compose.yml` | Available infrastructure for later tasks; task CRUD does not publish events |
| Frontend | `frontend/` | Static placeholder, not a completed application |

## Planned service evolution

Kafka producers/consumers, background workers, scheduler, mailer, or other
components may become separate deployable services when their behavior is
implemented and independent deployment has a concrete benefit. They must not
be described as current runtime boundaries before then.
