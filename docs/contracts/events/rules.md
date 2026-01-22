# Event Rules

## 1) Immutability
Events are immutable facts. Do not edit historical events.

## 2) Required envelope fields
Every event MUST include:
- event_id: UUID (idempotency key)
- type: string (routing/filtering)
- occurred_at: ISO8601 datetime (when the fact happened)

## 3) Delivery semantics: at-least-once
Duplicates are possible. Consumers MUST be idempotent.

### Idempotency guidance
For side effects (like sending emails):
- store processed event_id (e.g., table `processed_events`)
- if event_id already processed → skip
- commit Kafka offset only after successful side effect

## 4) Compatibility rules (schema evolution)
- Backward-compatible change: add optional fields only.
- Breaking change: do NOT rename/remove fields in place.
  Instead:
  - introduce a new event type name (recommended) OR
  - introduce version suffix in type (optional approach)
- Keep old consumers working until migrated.

## 5) Field naming
- snake_case for JSON keys (matches current contracts)
- UUID fields are strings formatted as UUID
