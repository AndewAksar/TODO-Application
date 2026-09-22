# Task 050 — JWT authentication flow

## Status

Completed.

Merged into main via PR #7: feat(auth): add JWT authentication flow.

Final squash commit:

93bb58c feat(auth): add JWT authentication flow

## Goal

Add the authentication foundation for the project.

The API must support user registration, user login, JWT access token issuing, and current-user resolution through a protected endpoint.

Core flow:

register user -> login user -> issue JWT -> send Bearer token -> restore current user -> use current user in protected routes

This task prepares the project for user-owned business logic, especially task CRUD.

## Why this task was needed

Before this task, the API did not have a reliable concept of the current user.

Without authentication, future task CRUD would be unsafe because the backend would not know:

* who is making the request;
* which user owns a task;
* which records the user is allowed to read;
* which records the user is allowed to update or delete.

This task introduced the identity layer required for all future user-owned operations.

## Scope completed

This task implemented the JWT authentication flow inside api_gateway.

Implemented areas:

* user model and database schema foundation;
* user repository methods;
* auth schemas;
* password hashing and verification;
* JWT creation and decoding;
* auth service layer;
* auth HTTP routes;
* current-user dependency;
* protected current-user endpoint;
* auth contract tests;
* auth unit tests;
* CI and Docker smoke improvements required to validate the auth flow.

## Main API routes

Implemented endpoints:

* POST /auth/register
* POST /auth/login
* GET /auth/me

## Main auth flow

Registration:

* client sends email and password;
* backend validates request schema;
* backend checks whether email already exists;
* backend hashes password;
* backend creates user;
* backend returns public user response;
* password_hash is not exposed.

Login:

* client sends email and password;
* backend finds user by email;
* backend verifies password;
* backend creates JWT access token;
* backend returns token response.

Current user:

* client sends Authorization: Bearer <token>;
* backend decodes JWT;
* backend extracts user_id;
* backend loads user from database;
* backend returns public user response.

## Implemented files and areas

Main application code:

* services/api_gateway/app/auth/routes.py
* services/api_gateway/app/auth/dependencies.py
* services/api_gateway/app/auth/schemas.py
* services/api_gateway/app/auth/service.py
* services/api_gateway/app/security/jwt.py
* services/api_gateway/app/security/passwords.py
* services/api_gateway/app/repositories/users.py
* services/api_gateway/app/models.py
* services/api_gateway/app/main.py

Database and infrastructure:

* services/api_gateway/migrations/versions/9a3b9f28e495_create_initial_schema.py
* docker-compose.yml
* infra/nginx/nginx.conf

Tests:

* tests/unit/test_auth_service.py
* tests/unit/test_auth_schemas.py
* tests/unit/test_jwt.py
* tests/unit/test_passwords.py
* tests/contract/test_auth_routes.py
* tests/contract/test_auth_dependency.py

CI:

* .github/workflows/ci.yml
* .github/workflows/docker-smoke.yml

## Business and security rules implemented

* User can register with email and password.
* User cannot register the same email twice.
* Password is stored only as hash.
* password_hash is never returned through HTTP responses.
* User can log in with valid credentials.
* User receives JWT access token after successful login.
* Protected endpoints require Authorization Bearer token.
* Missing token returns 401 Unauthorized.
* Invalid token returns 401 Unauthorized.
* Token for missing user returns 401 Unauthorized.
* Database infrastructure errors are converted to 503 Service Unavailable.
* JWT parsing is isolated from route logic.
* Current user resolution is reusable through get_current_user.

## HTTP behavior

POST /auth/register

Expected successful response:

* 201 Created
* returns public user response
* does not return password_hash

Expected error responses:

* 409 Conflict when email is already registered
* 503 Service Unavailable on database infrastructure error

POST /auth/login

Expected successful response:

* 200 OK
* returns access_token
* token_type is bearer

Expected error responses:

* 401 Unauthorized for invalid credentials
* 503 Service Unavailable on infrastructure error

GET /auth/me

Expected successful response:

* 200 OK
* returns current user from Bearer token
* does not return password_hash

Expected error responses:

* 401 Unauthorized without token
* 401 Unauthorized with invalid token
* 401 Unauthorized if token is valid but user no longer exists
* 503 Service Unavailable on database infrastructure error

## Important implementation decisions

### 1. AuthService owns business logic

Routes do not directly implement registration or login logic.

Routes delegate to AuthService.

AuthService is responsible for:

* checking duplicate email;
* hashing password;
* creating user;
* verifying credentials;
* issuing JWT;
* converting low-level failures into service-level exceptions.

### 2. UserRepository owns database operations

Repository methods are responsible for raw database access.

UserRepository provides:

* get_by_email
* get_by_id
* create_user

Routes and services do not write raw SQLAlchemy queries directly when repository methods already exist.

### 3. get_current_user is the reusable auth dependency

Protected routes should not decode JWT manually.

Instead, future routes must use:

current_user: Annotated[User, Depends(get_current_user)]

This is the key result of the auth task.

Future task CRUD must use this dependency to bind tasks to current_user.id.

### 4. HTTPBearer uses auto_error=False

This allows the project to control unauthorized responses manually.

Result:

* missing credentials return project-defined 401 response;
* invalid token returns the same 401 response;
* auth behavior is consistent across protected endpoints.

### 5. Auth exceptions are translated at the HTTP boundary

Service exceptions are not leaked directly to the client.

Routes convert service-layer errors into HTTP responses:

* EmailAlreadyRegisteredError -> 409 Conflict
* InvalidCredentialsError -> 401 Unauthorized
* AuthInfrastructureError -> 503 Service Unavailable

### 6. password_hash is never exposed

UserResponse is the public response schema.

It intentionally does not include password_hash.

This was verified by tests.

## CI and environment work completed during this task

This task also exposed and fixed several CI/environment problems.

### Dependency installation

Problem:

CI originally installed dependencies through pip by manually reading pyproject.toml.

This created dependency drift between local development, Docker, and GitHub Actions.

Fix:

CI was moved to uv.

Current model:

* setup Python
* install uv
* run uv sync --frozen --extra dev --extra api --extra test
* run checks through uv run

Result:

CI now uses uv.lock and runs with reproducible dependency versions.

### uv.lock usage

The project now treats uv.lock as the source of truth for exact dependency versions.

pyproject.toml describes dependency requirements.

uv.lock fixes the resolved dependency graph.

CI uses uv.lock through uv sync --frozen.

### PYTHONPATH

Problem:

After switching to uv run, pytest in CI could not import the project package path:

ModuleNotFoundError: No module named 'services'

Fix:

Added PYTHONPATH=. to CI checks.

Reason:

The project uses a monorepo-style layout where services/ lives in the repository root.

Python must see repository root as import root.

### Docker smoke

Problem:

docker-smoke checked the wrong protected endpoint:

/me

Actual endpoint:

/auth/me

Fix:

docker-smoke now checks /auth/me and expects 401 without token.

This validates that the protected endpoint is reachable and not accessible anonymously.

## Testing completed

Unit tests covered:

* password hashing;
* password verification;
* JWT creation;
* JWT decoding;
* auth schemas;
* AuthService registration flow;
* AuthService login flow;
* duplicate email behavior;
* invalid credentials behavior;
* token creation failure behavior;
* infrastructure error behavior.

Contract tests covered:

* POST /auth/register success;
* POST /auth/register duplicate email;
* POST /auth/login success;
* POST /auth/login invalid credentials;
* GET /auth/me with valid token;
* GET /auth/me without token;
* GET /auth/me with invalid token;
* GET /auth/me when user no longer exists;
* password_hash absence in HTTP responses.

CI checks completed:

* CI / checks
* CI / docker-tests
* CI / migration-check
* docker-smoke / docker-smoke

Manual verification completed:

* Docker environment started successfully.
* Alembic migrations applied.
* Swagger opened through nginx.
* User registration checked manually.
* Duplicate registration checked manually.
* Login checked manually.
* JWT token copied into Swagger authorization.
* GET /auth/me checked manually with valid Bearer token.
* GET /auth/me checked manually without token.
* GET /auth/me checked manually with invalid token.

## Non-scope

This task did not implement:

* refresh tokens;
* logout;
* roles;
* permissions;
* password reset;
* email verification;
* OAuth;
* task CRUD;
* Kafka events;
* outbox pattern;
* scheduler service;
* mailer service;
* frontend.

These are future tasks.

## Known limitations

The current auth implementation is intentionally minimal.

Known limitations:

* only access tokens are supported;
* no refresh token flow;
* no logout or token revocation;
* no roles or permissions;
* no password reset flow;
* no email confirmation;
* no account lockout policy;
* no rate limiting.

These limitations are acceptable for the current project stage.

## Result

The project now has a working authentication foundation.

The backend can:

* register users;
* hash passwords;
* authenticate users;
* issue JWT tokens;
* decode JWT tokens;
* restore current user from Bearer token;
* protect routes through get_current_user.

This enables the next task:

Task 060 — User-owned tasks CRUD

## Impact on next task

The next business feature must use the auth foundation from this task.

Task CRUD must not accept user_id from request body.

Instead, it must use:

current_user.id

from:

get_current_user

The core flow for the next task is:

JWT token -> get_current_user -> current_user.id -> create/list/update/delete only this user's tasks

## Retrospective notes

This task was larger than a simple auth route implementation because it exposed several infrastructure and CI concerns.

Important lessons:

* Auth is not only routes; it includes schemas, service layer, repository layer, password hashing, JWT, dependency injection, tests, Docker, and CI.
* CI must use the same dependency model as local development.
* uv.lock must be used in CI to avoid dependency drift.
* uv run ensures tools run inside the correct uv-managed environment.
* PYTHONPATH=. is required because the project imports from the repository-root services/ layout.
* Protected endpoints must be checked through their real route prefix.
* Swagger manual smoke is useful for validating the full path: nginx -> FastAPI -> auth route -> service -> database -> response.

## Definition of Done

This task is done because:

* /auth/register is implemented.
* /auth/login is implemented.
* /auth/me is implemented.
* get_current_user is implemented.
* JWT token creation and decoding work.
* password hashing and verification work.
* password_hash is not exposed.
* auth tests are present.
* CI is green.
* docker-smoke is green.
* manual Swagger smoke was completed.
* changes were merged into main.
