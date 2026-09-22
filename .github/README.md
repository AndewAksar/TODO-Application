# Repository Governance and CI Overview

## Current workflows

Both workflows run for pull requests and pushes to `main`.

### `ci.yml`

Current jobs are:

- **checks:** Python 3.12, locked `uv` dependency installation, Ruff lint,
  Ruff format check, mypy, and pytest with PostgreSQL integration tests excluded;
- **docker-tests:** runs `make test`, which starts the isolated `postgres-test`
  service, applies Alembic migrations, and runs the non-flaky test suite through
  `api-tooling` against the `todo_test` database and user;
- **migration-check:** starts a clean development PostgreSQL volume and applies
  `alembic upgrade head` through `api-tooling`.

The split keeps host-based code-quality checks and database-independent tests
independent of PostgreSQL, while the Docker job provides the database lifecycle
required by integration tests. The integration cleanup safety guard continues
to require the dedicated `todo_test` database and user.

A future CI is planned to move the PostgreSQL-backed integration suite from
`docker-tests` into a separate `integration` job.

### `docker-smoke.yml`

This workflow validates Compose configuration, builds images, starts the
runtime stack, waits for required services, checks API/Nginx HTTP availability,
and verifies that unauthenticated `GET /auth/me` returns `401`.

## Pull requests and ownership

Changes use the PR template, require review through CODEOWNERS, must remain
focused, and are expected to satisfy applicable repository policies. Current
governance sources include `AGENTS.md`, `CONTRIBUTING.md`,
`ENGINEERING_MANIFESTO.md`, accepted ADRs, and `docs/policies/`.
