# Data & Event Model

## Source of truth
- PostgreSQL is the system of record for all persistent state.
- Kafka is used for event propagation and async workflows (not for storing business state).

## Identifiers
- Prefer UUIDs for `user_id`, `task_id`, `event_id` (consistent across services).

## Kafka topics
- Main topic: `events`
- Multiple event types share the same topic → every event must include:
  - `type` (discriminator)
  - `event_id` (idempotency key)
  - `occurred_at` (ISO8601 datetime)

Details: `docs/contracts/events/topics.md`

## Event contracts
- Human-readable contracts: `docs/contracts/events/*`
- Machine-readable schemas: `services/shared/schemas/events/*`

### Delivery semantics
- at-least-once → duplicates are possible
- consumers must be idempotent

### Idempotency
Mailer must persist processed event ids (e.g., `processed_events(event_id, processed_at)`) and skip duplicates.

## Domain events (initial set)
- `task.created`
- `task.completed`
- `email.daily_digest.requested`

Catalog: `docs/contracts/events/event-catalog.md`

## Schema evolution rules (compatibility)
- Prefer backward-compatible changes (add optional fields).
- Breaking changes require a new version / type and explicit documentation updates.
Rules: `docs/contracts/events/rules.md`
