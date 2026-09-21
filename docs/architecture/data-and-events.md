# Data and Event Model

## Current database model

PostgreSQL is the system of record. The current API uses SQLAlchemy 2.0 async,
asyncpg, `create_async_engine`, and `async_sessionmaker(...,
expire_on_commit=False)`. Alembic revisions under
`services/api_gateway/migrations/versions/` are the schema-evolution record.

Accepted ADR 0004 defines integer entity identifiers:

- `User.id`: integer primary key;
- `Task.id`: integer primary key;
- `Task.user_id`: integer foreign key to `users.id` with `ON DELETE CASCADE`.

`User.tasks` and `Task.user` form a bidirectional ORM relationship. The user
side uses `all, delete-orphan` cascade.

Current Task fields are:

- `id`, `user_id`;
- `title` (required, up to 255 characters);
- nullable `description`;
- `is_done` (required, default false);
- nullable `done_at` and `due_at` timezone-aware timestamps;
- `created_at` and `updated_at` timezone-aware timestamps.

The current task index is `ix_tasks_user_id` on `user_id`. The earlier
`(user_id, done)` index was deliberately removed when `done` became `is_done`.

## Transactions and ownership
Repositories issue queries and `flush`/`refresh`/`delete` operations. Services
own write transaction completion: successful create/update/delete operations
commit and SQLAlchemy failures roll back. Read methods do not commit. All
individual-task repository lookups include both task ID and owner ID.

## Planned event model

**Status: Planned.** Task-domain Kafka publishing, outbox delivery, scheduler
production, mailer consumption, and machine-readable event schemas are not yet
implemented.

The proposed event design uses UUID `event_id` values as idempotency keys. This
does not change the accepted integer strategy for User and Task entity IDs.
The intended human-readable contracts are under `docs/contracts/events/`.
Their target machine-readable location is
`services/shared/schemas/events/`, which does not exist yet and is expected to
be addressed by Task 070.
