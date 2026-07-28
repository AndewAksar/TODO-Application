# Task Index

This folder contains the step-by-step development tasks for the project.

Each task describes a small, reviewable development step with clear scope,
non-scope, acceptance criteria, implementation plan, and required verification commands.

## Rules

- Follow tasks in order unless a task explicitly says otherwise.
- Each task must be small enough to fit into a focused pull request.
- Do not expand scope beyond what the task allows.
- Public API behavior must be covered by contract tests.
- Database schema changes must be implemented through Alembic migrations.
- Protected core rules are enforced via `AGENTS.md`.

## Completed project milestones

- Bootstrap repository structure and engineering standards.
- Docker Compose base infrastructure.
- FastAPI application base.
- Database session and Alembic setup.
- Initial database schema.
- JWT authentication flow:
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me`
  - `get_current_user`
  - protected endpoint behavior
- CI checks, Docker tests, migration check, and docker smoke flow.

## Current task

- 060 — User-owned task CRUD (`docs/tasks/060-user-owned-task-crud.md`)

## Next planned tasks

- 070 — Domain event contracts
- 080 — API Kafka producer
- 090 — API Outbox pattern
- 100 — Scheduler daily digest flow
- 110 — Mailer Kafka consumer
- 120 — Mailer idempotency
- 130 — Static frontend
- 140 — Final testing and docs
