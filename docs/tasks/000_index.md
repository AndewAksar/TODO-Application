# Task Index

Task files are historical implementation records and future work briefs. They
do not replace current architecture, API documentation, or accepted ADRs.

## Completed

- 050 — [JWT authentication](050_auth_jwt.md)
- 060 — [User-owned Tasks CRUD](060_user_owned_tasks_crud.md)
  - all five protected task routes;
  - owner-scoped service/repository behavior;
  - unit and HTTP contract tests;
  - real PostgreSQL integration-test layer.

## Next planned task

- 070 — [070_ci_cd_pipeline_foundation](080_domain_event_contracts.md) (`Status: Planned`)

## Reserved future task files

The following files are empty reservations and are not implemented features:

- 080 - domain event contracts
- 090 — API Kafka producer
- 100 — API outbox pattern
- 110 — Scheduler daily digest flow
- 120 — Mailer Kafka consumer
- 130 — Mailer idempotency
- 140 — Static frontend
- 150 — Final testing and documentation

## Task rules

- Public HTTP behavior requires contract coverage.
- Schema changes use Alembic.
- Follow `AGENTS.md` and the task's explicit writable/non-scope boundaries.
- Completed implementation work must include documentation-impact review.
