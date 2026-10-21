# Documentation Index

This index separates current architecture, operational guidance, contracts,
historical implementation records, and future plans.

## Current architecture

- [Architecture overview](architecture/overview.md)
- [Services and responsibilities](architecture/services.md)
- [Data and event model](architecture/data-and-events.md)
- [Local development](architecture/local-development.md)

## API

- [Tasks CRUD semantics](api/tasks.md)
- FastAPI Swagger at `/docs` is the formal machine-readable contract for
  implemented HTTP endpoints.

## Tasks and implementation history

- [Task index](tasks/000_index.md)
- [Task 050 — JWT authentication](tasks/050_auth_jwt.md)
- [Task 060 — User-owned tasks CRUD](tasks/060_user_owned_tasks_crud.md)
- [Task 070 — planned domain event contracts](tasks/080_domain_event_contracts.md)

Task documents preserve implementation history. They do not replace current
architecture or API documentation.

## Architectural decisions

- [ADR 0001 — repository governance](adr/0001_repository_governance_model.md)
- [ADR 0002 — CI checks versus Docker smoke](adr/0002_ci_strategy_checks_vs_smoke.md)
- [ADR 0003 — JWT authentication](adr/0003_authentication_strategy_jwt.md)
- [ADR 0004 — integer primary keys](adr/0004_primary_key_strategy_integer.md)
- [ADR 0005 — async database access](adr/0005_async_db_access_strategy.md)
- [ADR 0006 — AI agent integration](adr/0006_ai_agent_integration_model.md)
- [ADR 0007 — runtime/tooling separation](adr/0007_runtime_vs_tooling_container_separation.md)

## Policies

- [Migration policy](policies/MIGRATION_POLICY.md)
- [Testing policy](policies/TESTING_POLICY.md)
- [Security policy](policies/SECURITY_POLICY.md)
- [Observability policy](policies/OBSERVABILITY_POLISY.md)

## Current runbooks

- [Migration overview](runbooks/db_migration.md)
- [Generate migrations](runbooks/migration/migration_generation.md)
- [Apply migrations](runbooks/migration/migration_apply.md)
- [Migration debugging](runbooks/migration/migration_debugging.md)
- [Migration recovery](runbooks/migration/migration_recovery.md)
- [JWT auth flow](runbooks/jwt/auth_flow.md)
- [JWT debugging](runbooks/jwt/jwt_debugging.md)
- [Unit tests](runbooks/testing/unit_tests.md)
- [HTTP and event contract tests](runbooks/testing/contract_tests.md)
- [PostgreSQL integration tests](runbooks/testing/integration_tests.md)

Older auth/JWT documents under `runbooks/security/` are retained as historical
redirects to the canonical `runbooks/jwt/` guides.

## Contracts

- [Planned Kafka event contracts](contracts/events/README.md)
- [Planned event catalog](contracts/events/event-catalog.md)
- [Event compatibility rules](contracts/events/rules.md)
- [Planned topic layout](contracts/events/topics.md)

Event documentation is planned until Task 070 supplies and validates the
machine-readable schemas and runtime producers/consumers.

## Roadmap and historical specifications

- [Roadmap — planned work](../ROADMAP.md)
- [Original technical specification with current-state clarifications](../TASK.md)
- [Bootstrap checklist](runbooks/bootstrap.md) — historical repository setup
