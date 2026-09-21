# Event Contracts (Kafka)

## Status: Planned

This directory records the intended Kafka contract direction for Task 070 and
later work. It does not prove that task producers, scheduler producers, mailer
consumers, topics, or schema validation are operational.

## Intended contract model

An event contract will define type names, payload meanings, compatibility
rules, and topic use. Proposed delivery is at-least-once, so future consumers
must be idempotent.

Human-readable proposals are in this directory. The intended machine-readable
location is `services/shared/schemas/events/`, but that directory and its JSON
Schema files do not exist yet. Creating and testing those artifacts belongs to
Task 070; references in the catalog are target paths.

When implemented, a safe contract change will require:

1. an implemented JSON Schema;
2. matching catalog semantics;
3. positive and negative contract tests;
4. compatibility/version handling for breaking changes.
