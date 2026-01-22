# Event Contracts (Kafka)

This folder defines the **public contract** for Kafka events used in the system.

## What is a contract?
A contract is a stable agreement between producers and consumers:
- event type names
- payload structure and field meanings
- compatibility rules
- topic usage

## Source of truth
- Human-readable docs: `docs/contracts/events/*`
- Machine-readable schemas: `services/shared/schemas/events/*.schema.json`

## How to change events safely
1) Update the relevant JSON Schema.
2) Update `event-catalog.md` (meaning, producers/consumers).
3) Update tests (producer serialization + consumer parsing/handling).
4) If change is breaking: follow the compatibility rules in `rules.md`.

## Delivery semantics
Kafka is at-least-once → duplicates are possible.
Consumers MUST be idempotent (see `rules.md`).
