# Event Catalog

This catalog defines the meaning and usage of each event.

---

## 1) task.created

### Meaning
A new task was created for a user.

### Produced by
- API service (when a task is successfully created in PostgreSQL)

### Consumed by
- (optional now) Mailer / Analytics (future)

### Payload (contract)
See schema: `services/shared/schemas/events/task.created.schema.json`

### When emitted
After the task is committed to the database (PostgreSQL is source of truth).

---

## 2) task.completed

### Meaning
A task was marked as done.

### Produced by
- API service (when task.done transitions to true)

### Consumed by
- (optional) Analytics (future)

### Payload (contract)
See schema: `services/shared/schemas/events/task.completed.schema.json`

### When emitted
After DB commit.

---

## 3) email.daily_digest.requested

### Meaning
A daily email digest should be sent to the user (integration event).

### Produced by
- Scheduler service (daily at 00:00)

### Consumed by
- Mailer service (sends an email)

### Payload (contract)
See schema: `services/shared/schemas/events/email.daily_digest.requested.schema.json`

### Processing rules
- MUST be handled idempotently using event_id
- Kafka offset commit only after successful send
