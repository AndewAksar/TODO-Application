# Local Development

## Status: Current

Docker Compose is the canonical runtime/tooling environment. Host-side local
targets also exist, but require a prepared virtual environment and an explicit
`DATABASE_URL`.

## Prerequisites and environment

Install Git, Make, Docker, and Docker Compose. Copy the example environment:

```bash
cp .env.example .env
```

With that file, development PostgreSQL is exposed on host port `5434` and test
PostgreSQL on `5435`; containers connect internally on port `5432`. Without an
override, Compose's development port fallback is `5432`. Values in the example
are development-only and secrets must be replaced outside local development.

## Runtime environment

```bash
make build
make up
make ps
make logs
```

`make up` starts PostgreSQL, Kafka/Zookeeper, API, scheduler and mailer
containers, Nginx, and the static placeholder. Container availability is not a
claim that the planned Kafka/scheduler/mailer product flows are implemented.

Stop and remove volumes with:

```bash
make down
```

This deletes local Compose data, so use it intentionally.

## Development database migrations

```bash
make migrate
make makemigration M="describe schema change"
```

Both use the `api-tooling` container. New revisions appear under
`services/api_gateway/migrations/versions/`. See the
[migration overview](../runbooks/db_migration.md).

## Isolated integration database

```bash
make test-db-up
make test-db-migrate
```

These start `postgres-test` and apply the real Alembic chain to database/user
`todo_test`. The test service is separate from the normal `todo` database.

## Verification commands

All following targets use `api-tooling`:

```bash
make test-unit
make test-contract
make test-integration
make test
make lint
make typecheck
```

`make test-integration` and `make test` depend on `test-db-migrate`. Unit and
contract targets use the same container image but remain database-independent.
The full target selects every non-flaky test, including integration tests.

Host-side variants are `make test-local`, `test-local-unit`,
`test-local-contract`, `test-local-integration`, `lint-local`, and
`typecheck-local`. Every local test target requires `DATABASE_URL`; use the
dedicated test database for integration execution.

## Current CI limitation

A dedicated job that provisions `postgres-test`, applies Alembic, and runs the
PostgreSQL integration marker is planned but not yet implemented. Current
workflow behavior is documented in `.github/README.md` and must not be treated
as the target CI separation.
