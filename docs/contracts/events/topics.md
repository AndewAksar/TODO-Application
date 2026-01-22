# Kafka Topics

## Topic: `events`
Purpose: a single topic that carries all domain + integration events.

Producers:
- API service (task.created, task.completed, ...)
- Scheduler service (email.daily_digest.requested)

Consumers:
- Mailer service (email.daily_digest.requested)
- (future) analytics/audit services

Notes:
- Since multiple event types share one topic, every message MUST contain:
  - `type`
  - `event_id`
  - `occurred_at`

Delivery:
- at-least-once → duplicates are possible
- consumers must be idempotent
