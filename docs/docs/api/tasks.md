# Tasks API Behavior

## Status: Implemented

FastAPI OpenAPI/Swagger (`/openapi.json` and `/docs`) is the formal
machine-readable contract for implemented paths, HTTP methods, schemas, types,
and generated validation constraints. This document explains ownership and
business semantics rather than reproducing that specification.

## Endpoints

All task endpoints require a valid Bearer JWT:

| Method | Path | Success |
|---|---|---|
| `POST` | `/tasks` | `201 Created` |
| `GET` | `/tasks` | `200 OK` |
| `GET` | `/tasks/{task_id}` | `200 OK` |
| `PATCH` | `/tasks/{task_id}` | `200 OK` |
| `DELETE` | `/tasks/{task_id}` | `204 No Content` |

Missing/invalid credentials and users that no longer exist produce `401
Unauthorized` through the shared auth dependency. Database infrastructure
failures exposed by task operations produce `503 Service Unavailable`.

## Ownership

The client never chooses task ownership. `user_id` is absent from create/update
request schemas, and extra fields are forbidden. The API obtains the
authenticated `User` from `get_current_user` and passes `current_user.id` to
`TaskService`. Repository reads for a single task filter by both `task_id` and
`user_id`.

For get, update, and delete, a nonexistent task and another user's task both
produce `404 Not Found` with the same response. This prevents disclosure of a
foreign task's existence. List returns only the current user's tasks.

Task responses include the stored integer `user_id`; that response field does
not allow the client to assign or transfer ownership.

## Create semantics

Create accepts `title`, optional `description`, and optional `due_at`. It does
not accept `user_id`, `is_done`, or `done_at`. New tasks use `is_done = false`
and `done_at = null`.

`title` is trimmed, required, and limited to 255 characters. `due_at` must be a
timezone-aware datetime when present.

## PATCH semantics

Allowed fields are `title`, `description`, `due_at`, and `is_done`.

- An omitted field is unchanged.
- Explicit `null` clears nullable `description` and `due_at`.
- Explicit `null` is rejected for `title` and `is_done`; they may be omitted
  but cannot be cleared.
- Unknown fields, including `user_id`, are rejected.
- An empty object is valid and leaves business fields unchanged, while the
  current implementation still performs the normal update/commit path.

## Completion transitions

The service uses an injectable UTC clock so completion behavior is
deterministic in tests:

| Previous | Requested | `done_at` result |
|---|---|---|
| `false` | `true` | Set to the injected current time |
| `true` | `false` | Cleared to `null` |
| `true` | `true` | Existing value is preserved |
| `false` | `false` | Value is unchanged (normally `null`) |

Changing unrelated fields does not alter `is_done` or `done_at`.
