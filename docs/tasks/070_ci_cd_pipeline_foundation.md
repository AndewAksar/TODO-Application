# Task 070 — CI/CD pipeline foundation

## Status

Planned.

## Goal

Build a complete CI/CD foundation for the project.

The project must have a clear and reproducible path from source-code change to a verified application running on the deployment server.

Target flow:

`developer change`
→ `pull request`
→ `CI checks`
→ `merge to main`
→ `deployment pipeline`
→ `server update`
→ `database migrations`
→ `application restart`
→ `health verification`

The task must not only automate deployment, but also make the full CI/CD process understandable, observable, safe, and documented.

## Why this task is needed

The project already has a working CI foundation.

Current automated checks include:

* Ruff lint;
* Ruff format check;
* mypy;
* pytest;
* PostgreSQL-backed integration testing;
* Alembic migration verification;
* Docker smoke checks.

Task 060 also introduced a real isolated PostgreSQL integration-test environment using `postgres-test` / `todo_test`.

However, the current automation stops at verification.

After code is merged into `main`, there is no complete automated deployment path that:

* delivers the new application version to a server;
* prepares runtime configuration;
* applies database migrations;
* restarts the application;
* verifies that the new version is actually healthy;
* provides a documented recovery path when deployment fails.

The project therefore has CI elements, but does not yet have a complete CI/CD pipeline.

## Learning objective

This task is also an infrastructure-learning task.

Before implementation, the following concepts must be understood from general to specific:

* what Continuous Integration is;
* what Continuous Delivery is;
* what Continuous Deployment is;
* what a pipeline is;
* what a workflow, job, and step are;
* where GitHub Actions commands actually run;
* what triggers a workflow;
* what environment variables and secrets are;
* how Docker participates in CI/CD;
* how application code reaches the deployment server;
* how migrations are applied safely;
* what happens when deployment fails;
* what rollback means.

Implementation must follow understanding rather than replacing it.

## Current CI state

At the start of this task the project already has several automated checks.

The current logical structure is approximately:

`checks`
→ code-quality checks
→ database-independent tests

`docker-tests`
→ Docker-based test execution
→ PostgreSQL integration environment

`migration-check`
→ clean PostgreSQL
→ `alembic upgrade head`

`docker-smoke`
→ build runtime stack
→ start containers
→ wait for health
→ HTTP smoke verification

This task may restructure these jobs where necessary, but must preserve or improve their existing coverage.

## Target CI structure

The desired CI structure is:

### checks

Purpose:

Fast verification that does not require PostgreSQL infrastructure.

Expected responsibilities:

* install dependencies from `uv.lock`;
* Ruff lint;
* Ruff format check;
* mypy;
* unit tests;
* HTTP contract tests.

Integration tests must not run here.

### integration

Purpose:

Verify real persistence behavior against PostgreSQL.

Expected flow:

`postgres-test`
→ wait until healthy
→ `alembic upgrade head`
→ `todo_test`
→ PostgreSQL integration tests
→ cleanup

The existing database safety guard must remain active.

Integration cleanup must continue to refuse destructive operations unless:

`current_database() == "todo_test"`

and:

`current_user == "todo_test"`

### migration-check

Purpose:

Verify that the complete Alembic chain can initialize a clean database.

Expected flow:

clean PostgreSQL
→ apply `alembic upgrade head`
→ success/failure

This remains separate from integration tests.

### docker-smoke

Purpose:

Verify that the runtime stack can actually be built and started.

Expected checks include:

* Compose configuration is valid;
* images build;
* required containers start;
* health checks pass;
* API responds;
* Nginx responds;
* protected endpoints remain protected.

## Target CD structure

After CI succeeds and approved changes reach `main`, the deployment path must eventually become:

`main`
→ successful CI
→ start deployment
→ authenticate to deployment server
→ obtain exact application version
→ prepare runtime configuration
→ build or obtain Docker images
→ apply Alembic migrations
→ start/restart application
→ wait for health
→ perform post-deployment smoke checks
→ deployment success

Deployment must fail visibly if any mandatory step fails.

## Deployment architecture

Before implementing CD, inspect the actual target server and choose the simplest architecture appropriate for this project.

The first production-style deployment is expected to use approximately:

* Linux server;
* Docker;
* Docker Compose;
* GitHub Actions;
* SSH or another explicitly chosen secure deployment mechanism;
* environment variables or server-side `.env`;
* PostgreSQL persistent volume;
* health checks.

Do not introduce infrastructure platforms that are not needed for the current project stage.

## Scope

This task includes:

* study and documentation of CI/CD fundamentals required for implementation;
* final normalization of the existing CI structure;
* separation of database-independent and PostgreSQL-backed tests;
* dedicated PostgreSQL integration CI execution;
* deployment-server preparation requirements;
* deployment configuration;
* secure transfer/use of deployment credentials;
* automated deployment after successful changes to `main`;
* application startup/restart during deployment;
* Alembic migration execution during deployment;
* deployment health verification;
* failure handling;
* initial rollback procedure;
* CI/CD documentation;
* deployment runbooks;
* documentation-impact review.

## Non-scope

Do not implement unless separately approved:

* Kubernetes;
* Docker Swarm;
* Terraform;
* Ansible;
* Jenkins;
* Argo CD;
* multi-node orchestration;
* blue/green deployment;
* canary deployment;
* autoscaling;
* multiple production environments;
* high-availability PostgreSQL;
* managed Kubernetes;
* custom container registry infrastructure;
* complex secret-management platforms;
* domain events;
* Kafka producer implementation;
* outbox pattern;
* scheduler;
* mailer;
* frontend feature development.

The goal is a reliable first CI/CD implementation, not enterprise infrastructure for its own sake.

## Security rules

Deployment credentials and production secrets must never be committed to the repository.

Sensitive values may include:

* SSH credentials;
* deployment-server credentials;
* PostgreSQL password;
* `DATABASE_URL`;
* `JWT_SECRET_KEY`;
* future external-service credentials.

The implementation must explicitly define where every secret lives.

GitHub repository secrets and/or protected server-side environment configuration may be used where appropriate.

Production secrets must not appear in:

* source code;
* Docker images;
* committed `.env` files;
* CI logs;
* documentation examples containing real credentials.

## Database rules

Production deployment must use Alembic migrations.

Do not initialize production schema using:

`Base.metadata.create_all()`

Expected deployment flow:

application version selected
→ database connection available
→ `alembic upgrade head`
→ application startup/restart

Migration failure must stop deployment.

The task must document what state the application remains in if migration fails.

## Manual deployment milestone

Automatic deployment must not be implemented before the deployment procedure can be performed manually and understood.

The manual deployment milestone should prove that the team can:

1. connect to the server;
2. obtain the required application version;
3. provide runtime configuration;
4. build/start the containers;
5. connect to the intended PostgreSQL database;
6. apply Alembic migrations;
7. start the API;
8. verify `/health`;
9. verify application access through the intended public entry point;
10. inspect logs when something fails.

Only after this path works manually should it be automated.

## Deployment failure behavior

The pipeline must handle at least the following failure classes:

* CI failure;
* server unavailable;
* authentication failure;
* Docker build failure;
* migration failure;
* container startup failure;
* health-check failure;
* post-deployment smoke failure.

A failed deployment must produce a clear failed workflow result.

The pipeline must not report success merely because files reached the server.

## Rollback

The project must have a documented initial rollback procedure.

At minimum it must answer:

* how the previously working application version is identified;
* how that version is restored;
* how containers are restarted;
* how application health is rechecked;
* what to do if the failed deployment included a database migration.

Automatic rollback is not mandatory for the first implementation.

A reliable manual rollback procedure is acceptable.

## Observability during deployment

Deployment should provide enough information to answer:

* which commit/version was deployed;
* when deployment started;
* whether migrations completed;
* whether containers started;
* whether health verification passed;
* where to inspect application logs after failure.

Secrets must not be printed while providing this visibility.

## Read-only areas

Before implementation inspect:

* `AGENTS.md`
* `README.md`
* `ROADMAP.md`
* `.github/README.md`
* `.github/workflows/ci.yml`
* `.github/workflows/docker-smoke.yml`
* `docker-compose.yml`
* `Makefile`
* `.env.example`
* `pyproject.toml`
* `uv.lock`
* `services/api_gateway/Dockerfile`
* `services/api_gateway/alembic.ini`
* Alembic migration configuration
* health-check implementation
* relevant architecture documentation
* relevant testing runbooks
* relevant security policies

Files become writable only when explicitly authorized for the corresponding implementation step.

## Expected writable areas

Across the complete Task 070 implementation, expected writable areas may include:

* `.github/workflows/`
* `.github/README.md`
* `Makefile`
* `docker-compose.yml` or deployment-specific Compose configuration if required;
* `.env.example`;
* deployment scripts if introduced;
* `infra/`;
* CI/CD documentation;
* deployment runbooks;
* `README.md`;
* `ROADMAP.md`;
* `docs/tasks/000-index.md`;
* `docs/tasks/070_ci_cd_pipeline_foundation.md`;
* ADR files when an architecture decision requires one.

Each implementation subtask must narrow its own Writable list before editing.

## Implementation plan

### Step 0 — CI/CD fundamentals

Study the concepts needed to understand the implementation.

No infrastructure change yet.

Result:

The complete pipeline can be explained from developer commit to running application.

### Step 1 — Audit current CI

Inspect current workflows and identify:

* duplicate checks;
* responsibility of each job;
* PostgreSQL requirements;
* Docker requirements;
* dependency installation;
* workflow triggers;
* unnecessary coupling.

Produce the target CI layout before editing workflows.

### Step 2 — Separate CI responsibilities

Move toward:

`checks`
→ lint + format + typecheck + database-independent tests

`integration`
→ PostgreSQL integration tests

`migration-check`
→ Alembic chain

`docker-smoke`
→ runtime container smoke

Avoid unnecessary duplicate execution.

### Step 3 — Verify final CI

All CI jobs must be independently understandable and green.

Failure of one layer must clearly indicate which type of validation failed.

### Step 4 — Design deployment architecture

Determine:

* deployment server;
* deployment user;
* application directory;
* networking;
* exposed ports;
* persistent volumes;
* production PostgreSQL location;
* environment configuration;
* SSH model;
* source/image delivery strategy.

Record important decisions before automation.

### Step 5 — Prepare server

Prepare the server with the minimum required runtime environment.

Verify Docker and Compose operation.

Verify permissions and application directories.

### Step 6 — Configure secrets

Create the required GitHub/server-side secret model.

Ensure no real credentials enter repository history.

### Step 7 — Perform first manual deployment

Deploy the application manually using the exact intended future deployment procedure.

Document every required command and dependency.

### Step 8 — Add deployment workflow

Automate the proven manual procedure.

The workflow must deploy an exact known revision rather than an ambiguous working tree state.

### Step 9 — Add migration stage

Ensure deployment applies Alembic migrations safely.

Migration failure must stop further deployment.

### Step 10 — Add health verification

After deployment:

* wait for containers;
* verify application health;
* perform required smoke checks.

The job succeeds only after these checks pass.

### Step 11 — Add failure diagnostics

Provide useful logs/status without leaking secrets.

### Step 12 — Define rollback procedure

Verify that a previous application version can be restored.

Document database-migration limitations of rollback.

### Step 13 — Documentation and ADR review

Update all affected current-state documentation.

Create an ADR if deployment architecture or secret-management decisions meet ADR criteria.

### Step 14 — Final end-to-end verification

Verify the full path:

`PR`
→ CI
→ merge
→ deployment
→ migrations
→ healthy application

## Acceptance criteria

Task 070 is accepted when:

* CI responsibilities are clearly separated;
* unit/contract checks do not depend on PostgreSQL;
* PostgreSQL integration tests use only the isolated test database;
* integration safety guards remain active;
* Alembic migration verification remains independent;
* Docker smoke remains functional;
* deployment server requirements are documented;
* secrets are kept outside Git;
* manual deployment has been successfully performed;
* automated deployment can deploy an approved revision from `main`;
* production migrations are applied through Alembic;
* deployment stops on migration failure;
* deployment verifies application health;
* failed deployments are visible as failed;
* a rollback procedure exists;
* the deployed version can be identified;
* CI/CD documentation reflects actual behavior;
* documentation-impact review is complete.

## Verification commands

Exact commands may be refined during implementation because deployment-server details are not yet part of this task file.

Expected local/project verification includes:

* `make lint`
* `make typecheck`
* `make test-unit`
* `make test-contract`
* `make test-integration`
* `make test`
* `docker compose config`
* Docker build/start smoke verification
* `git diff --check`

CI verification must include all final workflow jobs.

Deployment verification must include a real deployment to the selected server and post-deployment health check.

## Documentation impact

This task necessarily affects documentation.

At minimum review:

* `README.md`
* `.github/README.md`
* `ROADMAP.md`
* `docs/architecture/`
* `docs/runbooks/`
* `docs/tasks/000-index.md`
* this task file
* relevant security documentation
* ADRs

The task cannot finish with `Documentation changes required: none`.

## Git / PR policy

Task 070 should be implemented through focused branches and reviewed commits rather than one uncontrolled repository-wide change.

Each implementation subtask must have its own explicit Task Brief before an AI agent modifies files.

Unless a subtask explicitly authorizes otherwise, the agent must:

* modify only explicitly writable files;
* run required checks;
* leave changes for manual review;
* not commit;
* not push;
* not create or merge a PR.

## Definition of Done

Task 070 is complete only when the project has a working, documented path:

`pull request`
→ `CI validation`
→ `merge to main`
→ `automatic deployment`
→ `Alembic migrations`
→ `application startup`
→ `health verification`

Additionally:

* all required CI jobs are green;
* integration tests cannot target the normal development database;
* production credentials are not stored in Git;
* deployment failure is visible and stops the pipeline;
* manual rollback is documented and verified;
* current architecture and runbooks describe the actual deployed system;
* documentation-impact review is complete;
* final changes are merged into `main`.
