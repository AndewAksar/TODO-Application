# Task 060 — User-owned tasks CRUD

## Status: Completed

This file preserves the original implementation brief below. Current API
semantics live in `docs/api/tasks.md`; current architecture lives in
`docs/architecture/`.

## Completion record

Task 060 delivered the protected endpoint set originally requested:

* `POST /tasks`
* `GET /tasks`
* `GET /tasks/{task_id}`
* `PATCH /tasks/{task_id}`
* `DELETE /tasks/{task_id}`

The implemented flow is `get_current_user` → `current_user.id` → `TaskService`
→ owner-scoped `TaskRepository`. Client request schemas do not accept
`user_id`; missing and foreign tasks share the same not-found behavior.

The implementation consists of the existing Task ORM mapping and Alembic CRUD
migration, Pydantic task schemas, repository, service, FastAPI routes/router
registration, and Nginx forwarding. Services own commit/rollback boundaries;
repositories perform SQLAlchemy persistence operations without committing.

Completion transitions are:

| Previous | Requested | Result |
|---|---|---|
| `false` | `true` | `done_at` becomes the injected clock value |
| `true` | `false` | `done_at` becomes `null` |
| `true` | `true` | existing `done_at` is preserved |
| `false` | `false` | `done_at` remains unchanged (normally `null`) |

Completed verification coverage includes schema and service unit tests, HTTP
route contract tests, and PostgreSQL integration tests. The integration layer
uses `api-tooling`, `postgres-test`, database/user `todo_test`, Alembic to head,
guarded cleanup before/after each test, a function-scoped async engine,
multiple fresh sessions, and an injected deterministic clock.

Repository history records the focused Task 060 test and infrastructure
commits. This completion record does not claim that the currently configured CI
already has the planned dedicated PostgreSQL integration-test job.

## Goal

Add the first real business feature of the project: CRUD operations for tasks owned by the currently authenticated user.

After the JWT authentication flow, the API must be able to use get_current_user to bind task operations to the current user_id.

Core flow:

`JWT token` -> `get_current_user` -> `user_id` -> `operate only on this user's tasks`

## Scope

This task may modify or add files related to task CRUD inside the API gateway.

Allowed areas:

* `services/api_gateway/app/models.py`
* `services/api_gateway/app/main.py`
* `services/api_gateway/app/tasks/`
* `services/api_gateway/app/repositories/tasks.py`
* `services/api_gateway/migrations/versions/`
* `tests/unit/`
* `tests/contract/`
* `tests/integration/`
* `tests/conftest.py` or `tests/integration/conftest.py` when shared integration fixtures are needed
* `docker-compose.yml`
* `Makefile`
* `.env.example`
* `infra/nginx/nginx.conf`
* `README.md`
* `docs/tasks/000-index.md`
* `docs/tasks/060_user_owned_tasks_crud.md`

Expected new API routes:

* `POST /tasks`
* `GET /tasks`
* `GET /tasks/{task_id}`
* `PATCH /tasks/{task_id}`
* `DELETE /tasks/{task_id}`

## Non-scope

Do not implement event-driven behavior in this task.

Out of scope:

* Kafka producer
* Outbox pattern
* Domain event publishing
* Scheduler service
* Mailer service
* Daily digest flow
* LLM reports
* Frontend
* Tags
* Projects
* Subtasks
* Search
* Pagination
* Advanced filtering

This task is only about synchronous HTTP CRUD backed by PostgreSQL.

## Business rules

* A task belongs to exactly one user.
* user_id is never accepted from the request body.
* user_id is always taken from current_user.id.
* A user can create tasks only for himself.
* A user can list only his own tasks.
* A user can read only his own task.
* A user can update only his own task.
* A user can delete only his own task.
* Missing task and foreign task must both be returned as 404 Not Found.
* Unauthorized requests must return 401 Unauthorized.
* Database infrastructure errors must be converted to 503 Service Unavailable.

## Task fields

Expected task fields:

* `id`
* `user_id`
* `title`
* `description`
* `is_done`
* `done_at`
* `due_at`
* `created_at`
* `updated_at`

Required behavior:

* New tasks are created with is_done = false.
* New tasks are created with done_at = null.
* When is_done changes from false to true, done_at is set.
* When is_done changes from true to false, done_at is cleared.

## API behavior

### Create task

Endpoint:

POST /tasks

Request body example:

* `title`: Buy milk
* `description`: After work
* `due_at`: 2026-07-30T12:00:00Z

Expected response:

`201 Created`

The response body must contain the created task.

### List tasks

Endpoint:

`GET /tasks`

Expected response:

`200 OK`

The response must contain only tasks owned by the current user.

### Get task by id

Endpoint:

`GET /tasks/{task_id}`

Expected responses:

* `200 OK` for an existing task owned by the current user.
* `404 Not Found` for a missing task.
* `404 Not Found` for a task owned by another user.

### Update task

Endpoint:

PATCH /tasks/{task_id}

Allowed fields:

* `title`
* `description`
* `due_at`
* `is_done`

Expected responses:

* `200 OK` for an existing task owned by the current user.
* `404 Not Found` for a missing task.
* `404 Not Found` for a task owned by another user.

### Delete task

Endpoint:

`DELETE /tasks/{task_id}`

Expected responses:

* `204 No Content` for an existing task owned by the current user.
* `404 Not Found` for a missing task.
* `404 Not Found` for a task owned by another user.

## Constraints

* Reuse existing auth dependency: get_current_user.
* Do not duplicate JWT parsing logic in task routes.
* Keep HTTP concerns in routes.
* Keep business rules in TaskService.
* Keep raw database operations in TaskRepository.
* Do not expose internal infrastructure exceptions through HTTP responses.
* Do not expose another user's task existence.
* Use Alembic for schema changes.
* Integration tests must use real PostgreSQL through SQLAlchemy async + asyncpg; SQLite is not used as a substitute.
* Integration tests run from the existing `api-tooling` test runner.
* Provide a separate PostgreSQL test service and database: `postgres-test` / `todo_test`.
* The normal runtime database `todo` and the integration-test database `todo_test` must be isolated from each other.
* Unit and contract tests must remain independent of the database even though they run from the same `api-tooling` environment.
* The `todo_test` schema must be prepared from the real Alembic migration chain (`alembic upgrade head`), not `Base.metadata.create_all()`.
* Integration-test data must be explicitly cleaned between tests; prefer a simple deterministic cleanup strategy over nested transaction/savepoint machinery.
* Cleanup code must refuse to run unless the configured database is clearly the dedicated test database.
* Do not change existing task business logic merely to make integration tests pass. If integration tests reveal a production defect, report it explicitly before changing task implementation.
* Keep the implementation compatible with existing CI jobs.

## Acceptance criteria

* Task table exists in the database.
* Task model is mapped by SQLAlchemy.
* Task repository supports create, list, get, update, and delete operations.
* Task service enforces user ownership rules.
* Task routes are protected by JWT auth.
* POST /tasks creates a task for the current user.
* GET /tasks returns only current user's tasks.
* GET /tasks/{task_id} returns 404 for foreign tasks.
* PATCH /tasks/{task_id} updates only current user's tasks.
* DELETE /tasks/{task_id} deletes only current user's tasks.
* done_at is set when a task is marked done.
* done_at is cleared when a task is marked not done.
* Contract tests cover protected route behavior.
* Unit tests cover task service behavior.
* A dedicated PostgreSQL test environment exists for integration tests.
* Integration tests run against `postgres-test` / `todo_test`, not the normal `todo` database.
* The test database schema is created by applying Alembic migrations to head.
* Integration tests verify real persistence and user-ownership isolation across TaskService, TaskRepository, SQLAlchemy, asyncpg, and PostgreSQL.
* Integration-test cleanup leaves tests independent and deterministic.
* CI is green.

## Implementation plan

1. Inspect the existing Task model and current Alembic schema.
2. Adjust or create the task database model if needed.
3. Add Alembic migration for missing task table fields/indexes if needed.
4. Add task Pydantic schemas.
5. Add TaskRepository.
6. Add TaskService and service-level exceptions.
7. Add /tasks routes.
8. Include the tasks router in the FastAPI app.
9. Update nginx config if /tasks is not proxied.
10. Add unit tests for task service.
11. Add contract tests for task HTTP routes.
12. Extend the task test infrastructure with an isolated `postgres-test` service and `todo_test` database.
13. Wire the existing `api-tooling` test runner to the isolated test database for database-backed test runs, while keeping unit and contract tests database-independent.
14. Prepare the test schema through the real Alembic migration chain and add a safety guard preventing cleanup against a non-test database.
15. Add simple deterministic integration fixtures for real AsyncSession access, test users, and explicit database cleanup between tests.
16. Add PostgreSQL integration tests for task persistence and user-ownership isolation.
17. Run focused unit, contract, and integration verification commands.
18. Run full local verification commands.
19. Run manual Swagger smoke test with two users.
20. Open PR and wait for CI.

## Tests to add

Contract tests:

* POST /tasks without token returns 401.
* POST /tasks with token returns 201.
* GET /tasks returns only current user's tasks.
* GET /tasks/{task_id} returns 200 for own task.
* GET /tasks/{task_id} returns 404 for foreign task.
* PATCH /tasks/{task_id} returns 200 for own task.
* PATCH /tasks/{task_id} returns 404 for foreign task.
* DELETE /tasks/{task_id} returns 204 for own task.
* DELETE /tasks/{task_id} returns 404 for foreign task.

Unit tests:

* create_task assigns current_user.id.
* list_tasks returns user-owned tasks.
* get_task returns only user-owned task.
* update_task updates allowed fields.
* marking done sets done_at.
* marking not done clears done_at.
* missing or foreign task raises TaskNotFoundError.
* database errors become TaskInfrastructureError.

Integration tests:

* create_task persists a new task in PostgreSQL after commit.
* list_tasks returns only rows owned by the requested user.
* get_task returns an owned task from PostgreSQL.
* get_task for another user's task raises TaskNotFoundError.
* update_task persists ordinary field changes in PostgreSQL.
* changing is_done from false to true persists is_done = true and a deterministic done_at.
* changing is_done from true to false persists is_done = false and clears done_at to NULL.
* updating another user's task raises TaskNotFoundError and leaves the stored row unchanged.
* delete_task removes an owned task from PostgreSQL.
* deleting another user's task raises TaskNotFoundError and leaves the stored row present.
* Persistence assertions must re-read state from PostgreSQL where appropriate instead of trusting only an already-loaded ORM object.
* Integration tests must not exercise HTTP, JWT, Nginx, Kafka, scheduler, or mailer behavior.

## Commands to run

Required before PR:

* `make lint`
* `make typecheck`
* `make test-unit`
* `make test-contract`
* `make test-integration`
* `make test`

Recommended before PR:

* `docker compose up -d --build`
* apply Alembic migrations to the dedicated `todo_test` database
* verify the test database is isolated from the normal `todo` database
* `manual Swagger smoke through nginx` with two users

## Definition of Done

The final PR must include:

* short summary of implemented task CRUD;
* list of changed files;
* tests added or updated;
* dedicated PostgreSQL integration-test infrastructure (`postgres-test` / `todo_test`);
* confirmation that Alembic migrations prepare the test schema;
* confirmation that integration cleanup cannot target the normal development database;
* commands executed and their results;
* confirmation that unit, contract, and integration suites are green;
* confirmation that CI is green;
* confirmation that manual Swagger smoke with two users was completed.

The task is done only when the user can register, log in, get a JWT, and use that JWT to create, list, update, and delete only his own tasks.
