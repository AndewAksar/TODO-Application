# Services & Responsibilities

This document describes service boundaries, responsibilities, and interactions.

## Service inventory

| Service | Path | Responsibility | Owns data | Produces events | Consumes events |
|--------|------|----------------|----------|-----------------|----------------|
| TODO API | `services/todo-service` | CRUD tasks, mark done, main REST API | tasks | `task.created`, `task.completed` | (optional future) |
| Auth | `services/auth-service` | register/login, JWT issuing | users | `user.registered` (future) | (optional future) |
| Scheduler | `services/scheduler-service` | daily job at 00:00; builds digest payload | (none or digest-related tables) | `email.daily_digest.requested` | (optional future) |
| Mailer | `services/mailer-service` | send emails; idempotent consumers | `processed_events` | (optional: email.sent) | `email.daily_digest.requested` |
| API Gateway (optional) | `services/api-gateway` | reverse proxy / BFF; serve SPA; route APIs | none | none | none |
| Shared | `services/shared` | shared schemas, common types/utils | n/a | n/a | n/a |

## Notes on boundaries
- `services/shared` and `docs/contracts/*` are **protected core** and should not be modified unless required and justified (see `AGENTS.md`).
- "Owns data" means the service is responsible for the schema/migrations and rules for those tables.
- In a training monorepo, multiple services may connect to the same PostgreSQL instance; ownership is still a conceptual boundary.
