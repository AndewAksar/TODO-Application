# Runbook: DB migrations (Alembic) in Docker Compose

This project runs migrations manually (no auto-run on container startup).

Assumptions:
- docker compose service names: `api`, `postgres`
- Postgres user/db: `[POSTGRES_USER]` / `[POSTGRES_DB]`
- Alembic config + migrations live inside the api container at `/app/migrations`

---

## 0) Quick health check (optional)

#### See running containers
#### Tail API logs
```bash
  docker compose logs -n 100 api
```
```bash
  docker compose ps
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

#### Apply all pending migrations:
```bash
  docker compose exec api alembic upgrade head
```
#### Show current revision:
```bash
  docker compose exec api alembic current
```

## 3) Autogenerate a new migration (when models change).

#### NOTE: Always ensure migrations/env.py imports models so metadata is populated.

#### Generate a new revision:
```bash
  docker compose exec api alembic revision --autogenerate -m "describe change"
```
#### If initial migration:
```bash
  docker compose exec api alembic revision --autogenerate -m "init schema"
```
#### Apply all pending migrations:
```bash
  docker compose exec api alembic upgrade head
```
#### List migration history (optional):
```bash
  docker compose exec api alembic history --verbose
```

## 4) Verify DB state

#### Check tables exist:
```
  docker compose exec postgres psql -U [POSTGRES_USER] -d [POSTGRES_DB] -c "\dt"
```
#### Use the configured POSTGRES_USER.
```bash
  docker compose exec postgres env | grep POSTGRES
```
#### Check what models are registered in metadata
```bash
  docker compose exec api python -c "import app.models; from app.db import Base; print(sorted(Base.metadata.tables.keys()))"
```
