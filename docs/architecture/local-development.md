# Local Development (Planned)

This document describes the intended local development environment.

## Goals
- one-command startup via Docker Compose
- reproducible environment for Kafka + PostgreSQL + services
- stable CI pipeline

## Local runtime (target)
Docker Compose will run:
- PostgreSQL
- Kafka (and its required dependencies)
- services (todo/auth/scheduler/mailer/gateway)
- optional mail sink (e.g., MailHog) for safe email testing

## Networking (target)
- Services communicate with PostgreSQL via internal Docker network.
- Services communicate with Kafka via internal Docker network.
- Only gateway / TODO API may expose ports to the host for development.

## Environment variables
- Use `.env` locally and `.env.example` for documentation.
- Never commit secrets.

## Makefile
All common actions should be done via `make` targets:
- `make lint`, `make format`, `make typecheck`, `make test`, `make coverage`
- `make up`, `make down`, `make logs` (when compose is added)

## Status
At the moment, the repository has the bootstrap and documentation prepared, but services are not implemented yet.
This file will be updated once Docker Compose and initial service skeletons are added.
