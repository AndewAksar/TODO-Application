# Repository Governance and CI Overview

## Current workflows

Both workflows run for pull requests and pushes to `main`.

### `ci.yml`

Current jobs are:

- **checks:** Python 3.12, locked `uv` dependency installation, Ruff lint,
  Ruff format check, mypy, and unrestricted `pytest -q`;
- **docker-tests:** runs the default `api-tooling` test command through Compose;
- **migration-check:** starts a clean development PostgreSQL volume and applies
  `alembic upgrade head` through `api-tooling`.

This describes workflow configuration, not a claim that every job is already
correctly provisioned for the new PostgreSQL integration layer.

### `docker-smoke.yml`

This workflow validates Compose configuration, builds images, starts the
runtime stack, waits for required services, checks API/Nginx HTTP availability,
and verifies that unauthenticated `GET /auth/me` returns `401`.

## Known CI follow-up

Dedicated PostgreSQL integration-test CI execution is planned but not yet
implemented. The intended future job will start isolated `postgres-test`, apply
Alembic to database/user `todo_test`, and run only the PostgreSQL-backed
integration suite with its cleanup safety guard. Until the workflow changes,
documentation must not say that this dedicated job already exists.

## Pull requests and ownership

Changes use the PR template, require review through CODEOWNERS, must remain
focused, and are expected to satisfy applicable repository policies. Current
governance sources include `AGENTS.md`, `CONTRIBUTING.md`,
`ENGINEERING_MANIFESTO.md`, accepted ADRs, and `docs/policies/`.
