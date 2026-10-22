# Repository Governance and CI Overview

## Current workflows

The single `CI` workflow runs validation jobs for pull requests and pushes to `main`.
Image publication runs only for successful pushes to `main`.

### `ci.yml`

Current jobs are:

- **checks:** Python 3.12, locked `uv` dependency installation, Ruff lint,
  Ruff format check, mypy, and pytest with PostgreSQL integration tests excluded;
- **integration:** runs `make test-integration`, which starts the isolated
  `postgres-test` service, applies Alembic migrations, and runs only the
  non-flaky tests marked `integration` through `api-tooling` against the
  `todo_test` database and user;
- **migration-check:** starts a clean development PostgreSQL volume and applies
  `alembic upgrade head` through `api-tooling`;
- **docker-smoke:** validates Compose configuration, builds images, starts the
  runtime stack, waits for required services, checks API/Nginx HTTP availability,
  and verifies that unauthenticated `GET /auth/me` returns `401`;
- **publish-image:** waits for all four validation jobs, builds the API
  `runtime` image, tags it with the full commit SHA, and publishes it to
  `ghcr.io/andewaksar/todo-application-api`.

The split keeps host-based code-quality checks and database-independent tests
independent of PostgreSQL, while the Docker job provides the database lifecycle
required by integration tests. The integration cleanup safety guard continues
to require the dedicated `todo_test` database and user.

Pull requests never publish images. For pushes to `main`, `publish-image` runs
only after all validation jobs succeed. It uses the repository-scoped
`GITHUB_TOKEN` with job-level `packages: write` permission. Published images use
the full commit SHA as the version tag; no mutable `latest` tag is published.

## Pull requests and ownership

Changes use the PR template, require review through CODEOWNERS, must remain
focused, and are expected to satisfy applicable repository policies. Current
governance sources include `AGENTS.md`, `CONTRIBUTING.md`,
`ENGINEERING_MANIFESTO.md`, accepted ADRs, and `docs/policies/`.
