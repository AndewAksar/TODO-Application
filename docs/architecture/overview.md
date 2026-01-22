# Architecture Overview

This repository contains a production-style training project: an event-driven TODO application built with an async Python stack (FastAPI + Pydantic v2), PostgreSQL, Kafka, Docker Compose, and CI quality gates.

## Core principles (non-negotiable)
- **PostgreSQL is the single source of truth.**
- Kafka is a **transport / event log**, not a state store.
- Kafka delivery is **at-least-once** → duplicates are possible.
- Services are **loosely coupled** and communicate primarily via **events** (Kafka).
- Public contracts are defined in `docs/contracts/*`. Event schemas live in `services/shared/schemas/*`.

## Components (high level)
- **frontend/**: static placeholder for the future SPA client.
- **services/todo-service**: main REST API for task management (CRUD, "done" transitions).
- **services/auth-service**: user registration/login, JWT issuing.
- **services/scheduler-service**: daily (00:00) digest job; emits digest-request events.
- **services/mailer-service**: consumes events and sends emails; must be idempotent.
- **services/api-gateway**: optional gateway/BFF layer (planned; can be used to serve SPA + route APIs).
- **services/shared**: shared schemas/types; considered protected core.

## Event-driven flow (examples)

### A) Create task
1. Client calls TODO API to create a task.
2. TODO service stores the task in PostgreSQL.
3. TODO service emits `task.created` event to Kafka topic `events`.

### B) Daily digest
1. Scheduler service runs at 00:00 daily.
2. Scheduler queries PostgreSQL for user stats and undone tasks.
3. Scheduler emits `email.daily_digest.requested` event to topic `events`.
4. Mailer service consumes the event and sends an email.
5. Mailer enforces idempotency using `processed_events` (or equivalent mechanism).

## Diagram (conceptual)

```mermaid
flowchart LR
  SPA[frontend/index.html (placeholder)] -->|HTTP| GW[api-gateway (optional)]
  SPA -->|HTTP| TODO[todo-service]
  SPA -->|HTTP| AUTH[auth-service]

  TODO -->|produce events| KAFKA[(Kafka: topic 'events')]
  SCHED[scheduler-service] -->|produce digest event| KAFKA

  KAFKA -->|consume| MAIL[mailer-service]
  TODO --> DB[(PostgreSQL)]
  AUTH --> DB
  SCHED --> DB
  MAIL --> DB
