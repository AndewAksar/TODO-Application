# Runbook: DB migrations (Alembic) in Docker Compose

This project runs migrations manually (no auto-run on container startup).

Assumptions:
- docker compose service names: `api`, `api-tooling`, `postgres`
- Postgres user/db: `[POSTGRES_USER]` / `[POSTGRES_DB]`
- Alembic config path inside tooling container: `/app/services/api_gateway/alembic.ini`
- Migration scripts path: `/app/services/api_gateway/migrations`

> Standard workflow: use `api-tooling` as the primary migration workspace.
> Runtime container `api` is not the canonical place for migration generation/apply in local engineering workflow.
---

## 0) Quick health check (optional)

#### See running containers
```bash
  docker compose ps
```
#### Tail API logs
```bash
  docker compose logs -n 100 api
```

## 1) Rebuild & start stack (keep DB data)

#### Rebuild images and start containers:
```bash
  docker compose down -v
```
```bash
  docker compose up -d --build
```
#### Wait until Postgres is healthy:
```bash
  docker compose ps
```

## 2) Apply existing migrations (NO schema changes)

#### Use this when:
- containers were rebuilt
- images were updated
- schema did NOT change

#### Apply all pending migrations (canonical):
```bash
  make migrate
```

#### Equivalent direct command via tooling container:
```bash
  docker compose --profile test run --rm api-tooling alembic upgrade head
```
#### Show current revision:
```bash
  docker compose --profile test run --rm api-tooling alembic current
```

## 3) Generate a new migration (when models change)

#### NOTE: Always ensure migrations/env.py imports models so metadata is populated.

#### Generate a new revision (canonical):
```bash
  make makemigration M="describe change"
```
#### If initial migration:
```bash
  make makemigration M="init schema"
```
#### Apply all pending migrations after generation:
```bash
  make migrate
```
#### List migration history (optional):
```bash
  docker compose --profile test run --rm api-tooling alembic history --verbose
```

## 4) Verify DB state

#### Check tables exist:
```
  docker compose exec postgres psql -U [POSTGRES_USER] -d [POSTGRES_DB] -c "\\dt"
```
#### Use the configured POSTGRES_USER.
```bash
  docker compose exec postgres env | grep POSTGRES
```
#### Check what models are registered in metadata
```bash
  docker compose --profile test run --rm api-tooling python -c "import app.models; from app.db import Base; print(sorted(Base.metadata.tables.keys()))"
```
