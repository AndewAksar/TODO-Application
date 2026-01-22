# AGENTS.md — AI Agent (Codex) Operating Guide

This repository is a **training project in production style**: multi-user TODO app with REST API + SPA, microservices, Kafka (event-driven), JWT auth, async Python stack. The priority is **clarity of code** and **modern best practices**, suitable for a strong junior+/middle portfolio.

## 0) Project “truths” (must not be violated silently)
- **PostgreSQL is the single source of truth**. Kafka is **NOT** a state store. :contentReference[oaicite:3]{index=3}
- System is **event-driven**: significant state changes produce domain events.
- Services **do not call each other directly** (no synchronous inter-service RPC as the default). External effects (email) happen **only via events**. :contentReference[oaicite:4]{index=4}
- Kafka delivery semantics: **at-least-once** (duplicates are possible). :contentReference[oaicite:5]{index=5}

## 1) Repo map (high level)
- `services/api` — main REST API (FastAPI), writes to Postgres, produces domain events
- `services/auth` — registration/login, JWT issuance
- `services/scheduler` — daily cron logic, reads DB, produces digest events
- `services/mailer` — consumes events, sends emails, implements idempotency
- `services/shared` — shared schemas/types/utilities (may be changed if needed, but impact must be documented)
- `infra/*` — docker/kafka/nginx
- `docs/*` — architecture, contracts, ADR, runbooks
- `tests/*` — test suites

## 2) Tech stack (expected)
- Python 3.12+
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 async + Alembic
- PostgreSQL
- Kafka (producer/consumer)
- Docker Compose
- GitHub Actions
- pytest (+ coverage)

(Keep solutions modern but explainable. Prefer the simplest approach that is still correct.)

## 3) What the agent is allowed to change (YES, but with discipline)
The agent **may**:
- change REST contracts
- change Kafka event schemas
- add new services
- modify infra (docker/kafka/nginx)
- refactor existing code without an explicit task
- modify `services/shared` **only when explicitly required by the task**.
Changes to `services/shared` or `docs/contracts/*` are considered **high-impact**.
They require additional justification and safeguards (see section 3.1).

However, every such change must be **explicitly surfaced** in the output:
- what changed
- why it changed
- what breaks / migration steps (if any)
- what tests were updated/added

In other words: “YES to change” does **not** mean “silent breaking changes”.

## 4) Protected core: shared & contracts

The following directories form the **protected core of the system**:

- `services/shared`
- `docs/contracts/*`
- `services/shared/schemas/*`

### Default rule
By default, the agent MUST NOT modify the protected core.

### Allowed only if
The agent may modify the protected core **only if at least one condition is met**:
1) The task explicitly requests such a change, OR
2) The agent clearly explains why the change is unavoidable.

### Mandatory requirements
Any change to the protected core MUST include:
- a clear explanation of **why** the change is needed
- a list of **impacted services**
- updated or new **tests** covering the change
- updated documentation (contracts / catalog / rules)

Silent or undocumented changes to the protected core are forbidden.

## 5) Golden rules (non-negotiable)
1) **Clarity first**: readable code > clever code.
2) Prefer **small, incremental steps**: decompose work into tasks/subtasks.
3) **No random dependencies**: do not add a new dependency without a strong reason (and explain it).
4) **No logging format changes** unless explicitly requested.
5) **No directory reshuffles** unless explicitly requested (or you clearly justify and document it).
6) If you change contracts/schemas/infra: update docs and tests accordingly.
7) **Shared & contracts are stable by default**:
   do not change them unless the task explicitly requires it or you justify it clearly.

## 6) Required quality gate (must be run and reported)
Before finalizing any change, the agent MUST run and explicitly report:
- `make lint`  (ruff lint)
- `make format` (ruff format)
- `make typecheck` (mypy; may be gradual, but must not regress)
- `make test` (pytest)
- `make coverage` (coverage must be **>= 80%** overall, unless task explicitly allows temporary lower coverage)

**In the final message, include the exact commands you ran and their outcome.**
If commands cannot be run in the environment, state that explicitly and provide what would be run locally/CI.

## 7) Work format (how to execute tasks)
For each task the agent takes on, follow this structure:

### A) Plan (decomposition)
- List subtasks in order.
- Identify touched services/modules.
- Identify contracts/events impacted.

### B) Implementation constraints
- Keep diffs small.
- Prefer adding tests alongside changes.
- If refactoring: do it in a separate commit/subtask when possible.

### C) Deliverables (always)
- Short summary of changes
- List of changed files
- List of tests added/updated
- Commands executed + results

## 8) Contracts (REST + Events)
### REST
Minimum endpoints expected (may evolve): registration/login + CRUD tasks. :contentReference[oaicite:6]{index=6}

When changing REST:
- update `docs/contracts/` (or OpenAPI, if present)
- update API tests

### Kafka events
Events are JSON, immutable, include `event_id` and `occurred_at`. :contentReference[oaicite:7]{index=7}
Known event types include:
- `task.created` (TaskCreated)
- `task.completed` (TaskCompleted)
- `email.daily_digest.requested` (DailyDigestRequested) :contentReference[oaicite:8]{index=8}

When changing events:
- keep backward compatibility if possible (add fields rather than rename/remove)
- if breaking is necessary, bump version / change event type naming and document it
- update producer + consumer + tests

## 9) Scheduler rules (daily digest)
Scheduler runs daily (00:00), aggregates per-user stats, emits `DailyDigestRequested`, and **does not send emails directly**. :contentReference[oaicite:9]{index=9}

## 10) Mailer rules (idempotency is mandatory)
Mailer consumes from topic `events`. For `DailyDigestRequested`:
- check `event_id` (idempotency)
- send email
- persist `event_id` as processed
- commit offset only after successful send :contentReference[oaicite:10]{index=10}

For changes to `services/shared` or `docs/contracts/*`:
- contract tests are mandatory
- schema validation must not regress
- changes without tests are considered incomplete

Idempotency storage: `processed_events(event_id PK, processed_at)` :contentReference[oaicite:11]{index=11}

## 11) Testing expectations
- unit tests for domain logic
- API tests (FastAPI TestClient)
- integration tests are welcome if they are stable in Docker Compose :contentReference[oaicite:12]{index=12}

When adding a feature:
- add at least one unit test (if applicable)
- add/extend API test for endpoint behavior
- if events are produced/consumed, add tests for serialization/handling

## 12) Documentation expectations
Docs are part of the product. If you change behavior, update docs:
- `docs/architecture/` — system overview
- `docs/contracts/` — REST & events
- `docs/adr/` — when decision changes direction or introduces a new approach
- `docs/runbooks/` — how to operate/debug

## 13) Safety & secrets
- Never commit secrets.
- Use `.env` locally and `.env.example` for documentation.
- Log safely: do not log passwords/tokens.

— End of AGENTS.md
