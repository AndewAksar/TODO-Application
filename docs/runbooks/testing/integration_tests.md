# PostgreSQL Integration Test Runbook

## Status: Current

## Purpose and boundary

The current integration layer verifies the real persistence path:

```text
TaskService
→ TaskRepository
→ AsyncSession
→ SQLAlchemy async engine
→ asyncpg
→ postgres-test / todo_test
```

It deliberately does not exercise HTTP, JWT, Nginx, Kafka, scheduler, or
mailer. Those are different boundaries. Unlike unit/HTTP contract tests, this
layer does not replace PostgreSQL with mocks or SQLite.

## Environment

- Compose service: `postgres-test` (profile `test`)
- database: `todo_test`
- database user: `todo_test`
- runner: ephemeral `api-tooling` container
- connection inside Compose:
  `postgresql+asyncpg://todo_test:todo_test@postgres-test:5432/todo_test`
- schema setup: `alembic upgrade head`, never `Base.metadata.create_all()`

## Canonical commands

```bash
make test-db-up       # start postgres-test and wait for health
make test-db-migrate  # apply Alembic head to todo_test
make test-integration # migrate, then run the integration marker
```

`make test` also prepares the test database and runs every non-flaky test.

## Safety and cleanup

The autouse fixture cleans before and after each integration test with:

```sql
TRUNCATE TABLE tasks, users RESTART IDENTITY CASCADE
```

Before destructive cleanup it queries `current_database()` and `current_user`.
It refuses to proceed unless both equal `todo_test`. This protects the normal
development `todo` database even if a caller supplies the wrong URL.

The explicit cleanup strategy is intentionally simpler than nested
transactions/savepoints and makes committed service behavior observable.

## Fixture and session lifecycle

`integration_engine` is function-scoped. It creates one `AsyncEngine` from the
configured URL for a test and awaits `engine.dispose()` in teardown. The
session factory is built from that engine with `expire_on_commit=False`, which
matches application session behavior.

Each scenario may open multiple independent sessions from the same factory:

1. arrange data and commit;
2. invoke `TaskService`, whose create/update/delete methods perform real commits;
3. open a fresh verification session and re-read PostgreSQL state.

Fresh verification sessions prevent assertions from succeeding merely because
an already-loaded ORM object was mutated in memory.

## Deterministic time

Completion tests inject a fixed clock into `TaskService`. They verify that a
`false → true` transition persists the exact injected value and that reopening
a task clears `done_at`, without relying on wall-clock timing.

## Troubleshooting

1. Check `docker compose --profile test ps postgres-test`.
2. Re-run `make test-db-migrate` and inspect Alembic errors.
3. Confirm the URL targets `postgres-test/todo_test` from inside Compose.
4. Never weaken or bypass the database/user guard.
5. Use `make test-integration`; a direct host pytest command must supply an
   equivalent safe test URL and a migrated schema.

## CI status

Dedicated PostgreSQL integration-test CI execution is planned but not yet
implemented. The intended future job will provision the isolated database,
apply Alembic, and run this layer with the same safety guarantees.
