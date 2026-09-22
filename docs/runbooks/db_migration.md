# Database Migration Runbook Index

## Status: Current

This is the canonical entry point for project migrations. Detailed procedures
live in the specialized runbooks linked below; they are not duplicated here.

## Invariants

- Alembic runs through the ephemeral `api-tooling` container.
- The runtime `api` image is not the migration workstation.
- Revisions live in `services/api_gateway/migrations/versions/` and must appear
  in the host working tree.
- Development schema changes use the Alembic chain; do not use ad-hoc SQL or
  `Base.metadata.create_all()`.

## Everyday workflow

```bash
make up
make migrate
make makemigration M="describe schema change"
```

Review every generated revision before applying or committing it.

## Specialized procedures

- [Generate a revision](migration/migration_generation.md)
- [Apply, inspect, or downgrade revisions](migration/migration_apply.md)
- [Diagnose migration problems](migration/migration_debugging.md)
- [Recover a broken migration state](migration/migration_recovery.md)
- [Migration policy](../policies/MIGRATION_POLICY.md)

## Test database

`make test-db-migrate` starts `postgres-test` and applies the same Alembic head
to the isolated `todo_test` database. See the
[integration test runbook](testing/integration_tests.md) for its safety rules.
