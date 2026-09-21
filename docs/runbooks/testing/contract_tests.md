# Contract Test Playbook

## Status: Current

Contract tests protect observable interfaces without requiring a real database
or broker. The repository has two contract categories with different sources
of truth.

## Implemented HTTP adapter contracts

Current tests under `tests/contract/` exercise FastAPI routing, dependencies,
Pydantic validation, request/response behavior, status codes, and translation
of service errors. They use `TestClient`, override auth/session dependencies,
and replace service persistence calls where appropriate.

These tests answer questions such as:

- does a protected route reject missing credentials;
- does the route pass `current_user.id` rather than client ownership;
- do schemas reject forbidden/invalid fields;
- are not-found and infrastructure errors mapped to the documented HTTP status;
- does delete return an empty `204` response.

FastAPI OpenAPI is the formal machine-readable HTTP contract. Human semantic
rules for tasks are documented in `docs/api/tasks.md`.

## Planned event/schema contracts

**Status: Planned.** Task 070 is expected to establish machine-readable event
schemas and their positive/negative validation tests. The proposed
human-readable material is under `docs/contracts/events/`; target JSON Schema
paths under `services/shared/schemas/events/` do not exist yet.

When event schemas are implemented, tests should validate required fields,
types, valid examples, rejection cases, and compatibility/versioning rules.
They should not pretend that a producer or consumer exists merely because a
proposed document exists.

## Boundaries

A contract test:

- does not use real PostgreSQL or Kafka when validating only the adapter/schema;
- does not replace unit tests for service business logic;
- does not replace integration tests for real persistence;
- verifies stable behavior at a module/service boundary.

Not every contract must be a standalone external schema artifact: implemented
HTTP contracts are also defined by FastAPI/Pydantic/OpenAPI. Event contracts,
when implemented, require checked-in schemas because they cross asynchronous
producer/consumer boundaries.

## Running

```bash
make test-contract
```
The suite must remain deterministic and database-independent.
