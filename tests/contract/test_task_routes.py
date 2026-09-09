from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api_gateway.app.api.deps import get_session
from services.api_gateway.app.auth.dependencies import get_current_user
from services.api_gateway.app.models import Task, User
from services.api_gateway.app.tasks.routes import router
from services.api_gateway.app.tasks.service import (
    TaskInfrastructureError,
    TaskNotFoundError,
    TaskService,
)

pytestmark = [pytest.mark.unit, pytest.mark.contract]

CURRENT_USER_ID = 123
TASK_ID = 42
DUE_AT = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
CREATED_AT = datetime(2026, 9, 1, 8, 30, tzinfo=UTC)
UPDATED_AT = datetime(2026, 9, 2, 9, 45, tzinfo=UTC)
DONE_AT = datetime(2026, 9, 2, 9, 40, tzinfo=UTC)
SERVICE_UNAVAILABLE = {"detail": "Service temporarily unavailable"}
NOT_FOUND = {"detail": "Task not found"}


@pytest.fixture
def session_stub() -> object:
    return object()


def _make_user() -> User:
    return User(
        id=CURRENT_USER_ID,
        email="tasks@example.com",
        username="task-owner",
        password_hash="hashed_password",
        created_at=CREATED_AT,
    )


def _make_task(
    *,
    task_id: int = TASK_ID,
    title: str = "Buy milk",
    description: str | None = "After work",
    is_done: bool = False,
    done_at: datetime | None = None,
    due_at: datetime | None = DUE_AT,
) -> Task:
    return Task(
        id=task_id,
        user_id=CURRENT_USER_ID,
        title=title,
        description=description,
        is_done=is_done,
        done_at=done_at,
        due_at=due_at,
        created_at=CREATED_AT,
        updated_at=UPDATED_AT,
    )


def _task_json(task: Task) -> dict[str, object]:
    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "is_done": task.is_done,
        "done_at": task.done_at.isoformat().replace("+00:00", "Z") if task.done_at else None,
        "due_at": task.due_at.isoformat().replace("+00:00", "Z") if task.due_at else None,
        "created_at": task.created_at.isoformat().replace("+00:00", "Z"),
        "updated_at": task.updated_at.isoformat().replace("+00:00", "Z"),
    }


def _test_app(session_stub: object, *, authenticated: bool) -> FastAPI:
    app = FastAPI()

    async def fake_get_session() -> AsyncIterator[object]:
        yield session_stub

    app.dependency_overrides[get_session] = fake_get_session
    if authenticated:
        app.dependency_overrides[get_current_user] = _make_user
    app.include_router(router)
    return app


@pytest.fixture
def client(session_stub: object) -> Iterator[TestClient]:
    with TestClient(_test_app(session_stub, authenticated=True)) as test_client:
        yield test_client


@pytest.fixture
def anonymous_client(session_stub: object) -> Iterator[TestClient]:
    with TestClient(_test_app(session_stub, authenticated=False)) as test_client:
        yield test_client


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("POST", "/tasks", {"title": "Buy milk"}),
        ("GET", "/tasks", None),
        ("GET", "/tasks/42", None),
        ("PATCH", "/tasks/42", {"is_done": False}),
        ("DELETE", "/tasks/42", None),
    ],
)
def test_every_task_endpoint_requires_authentication(
    anonymous_client: TestClient,
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    response = anonymous_client.request(method, path, json=payload)

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_create_maps_request_to_service_and_serializes_task(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    session_stub: object,
) -> None:
    task = _make_task()

    async def fake_create_task(
        self: TaskService,
        *,
        user_id: int,
        title: str,
        description: str | None,
        due_at: datetime | None,
    ) -> Task:
        assert self._session is session_stub
        assert user_id == CURRENT_USER_ID
        assert title == "Buy milk"
        assert description == "After work"
        assert due_at == DUE_AT
        return task

    monkeypatch.setattr(TaskService, "create_task", fake_create_task)

    response = client.post(
        "/tasks",
        json={
            "title": "Buy milk",
            "description": "After work",
            "due_at": "2026-09-10T12:00:00Z",
        },
    )

    assert response.status_code == 201
    assert response.json() == _task_json(task)


def test_create_infrastructure_error_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        TaskService, "create_task", AsyncMock(side_effect=TaskInfrastructureError())
    )

    response = client.post("/tasks", json={"title": "Buy milk"})

    assert response.status_code == 503
    assert response.json() == SERVICE_UNAVAILABLE


def test_create_rejects_client_supplied_user_id_before_service(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    create_mock = AsyncMock()
    monkeypatch.setattr(TaskService, "create_task", create_mock)

    response = client.post("/tasks", json={"title": "Buy milk", "user_id": 999})

    assert response.status_code == 422
    create_mock.assert_not_awaited()


def test_list_maps_current_user_and_serializes_tasks(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    session_stub: object,
) -> None:
    tasks = [_make_task(), _make_task(task_id=43, title="Call dentist", due_at=None)]

    async def fake_list_tasks(self: TaskService, *, user_id: int) -> list[Task]:
        assert self._session is session_stub
        assert user_id == CURRENT_USER_ID
        return tasks

    monkeypatch.setattr(TaskService, "list_tasks", fake_list_tasks)

    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == [_task_json(task) for task in tasks]


def test_list_empty_returns_successful_empty_collection(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(TaskService, "list_tasks", AsyncMock(return_value=[]))

    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_infrastructure_error_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        TaskService,
        "list_tasks",
        AsyncMock(side_effect=TaskInfrastructureError()),
    )

    response = client.get("/tasks")

    assert response.status_code == 503
    assert response.json() == SERVICE_UNAVAILABLE


def test_get_maps_user_and_path_ids_and_serializes_task(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    session_stub: object,
) -> None:
    task = _make_task(is_done=True, done_at=DONE_AT)

    async def fake_get_task(self: TaskService, *, user_id: int, task_id: int) -> Task:
        assert self._session is session_stub
        assert user_id == CURRENT_USER_ID
        assert task_id == TASK_ID
        return task

    monkeypatch.setattr(TaskService, "get_task", fake_get_task)

    response = client.get("/tasks/42")

    assert response.status_code == 200
    assert response.json() == _task_json(task)


def test_get_not_found_error_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        TaskService,
        "get_task",
        AsyncMock(side_effect=TaskNotFoundError()),
    )

    response = client.get("/tasks/42")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_get_infrastructure_error_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        TaskService,
        "get_task",
        AsyncMock(side_effect=TaskInfrastructureError()),
    )

    response = client.get("/tasks/42")

    assert response.status_code == 503
    assert response.json() == SERVICE_UNAVAILABLE


def test_get_rejects_non_integer_path_before_service(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    get_mock = AsyncMock()
    monkeypatch.setattr(TaskService, "get_task", get_mock)

    response = client.get("/tasks/not-an-integer")

    assert response.status_code == 422
    get_mock.assert_not_awaited()


def test_patch_forwards_only_explicit_updates_and_serializes_task(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    session_stub: object,
) -> None:
    task = _make_task(description=None, is_done=False)

    async def fake_update_task(
        self: TaskService,
        *,
        user_id: int,
        task_id: int,
        **updates: object,
    ) -> Task:
        assert self._session is session_stub
        assert user_id == CURRENT_USER_ID
        assert task_id == TASK_ID
        assert updates == {"description": None, "is_done": False}
        return task

    monkeypatch.setattr(TaskService, "update_task", fake_update_task)

    response = client.patch("/tasks/42", json={"description": None, "is_done": False})

    assert response.status_code == 200
    assert response.json() == _task_json(task)


def test_patch_not_found_error_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        TaskService,
        "update_task",
        AsyncMock(side_effect=TaskNotFoundError()),
    )

    response = client.patch("/tasks/42", json={"title": "New title"})

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_patch_infrastructure_error_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        TaskService,
        "update_task",
        AsyncMock(side_effect=TaskInfrastructureError()),
    )

    response = client.patch("/tasks/42", json={"title": "New title"})

    assert response.status_code == 503
    assert response.json() == SERVICE_UNAVAILABLE


def test_patch_rejects_null_title_before_service(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    update_mock = AsyncMock()
    monkeypatch.setattr(TaskService, "update_task", update_mock)

    response = client.patch("/tasks/42", json={"title": None})

    assert response.status_code == 422
    update_mock.assert_not_awaited()


def test_delete_maps_user_and_path_ids_and_returns_empty_204(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    session_stub: object,
) -> None:
    async def fake_delete_task(self: TaskService, *, user_id: int, task_id: int) -> None:
        assert self._session is session_stub
        assert user_id == CURRENT_USER_ID
        assert task_id == TASK_ID

    monkeypatch.setattr(TaskService, "delete_task", fake_delete_task)

    response = client.delete("/tasks/42")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_not_found_error_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        TaskService,
        "delete_task",
        AsyncMock(side_effect=TaskNotFoundError()),
    )

    response = client.delete("/tasks/42")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_delete_infrastructure_error_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        TaskService,
        "delete_task",
        AsyncMock(side_effect=TaskInfrastructureError()),
    )

    response = client.delete("/tasks/42")

    assert response.status_code == 503
    assert response.json() == SERVICE_UNAVAILABLE
