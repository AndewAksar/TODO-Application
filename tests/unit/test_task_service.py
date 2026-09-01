from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from services.api_gateway.app.models import Task
from services.api_gateway.app.tasks.service import (
    TaskInfrastructureError,
    TaskNotFoundError,
    TaskService,
)
from sqlalchemy.exc import SQLAlchemyError

pytestmark = pytest.mark.unit

USER_ID = 7
TASK_ID = 42
FIXED_NOW = datetime(2026, 8, 18, 13, 0, tzinfo=UTC)
OLD_DONE_AT = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
OLD_DUE_AT = datetime(2026, 8, 20, 17, 0, tzinfo=UTC)
NEW_DUE_AT = datetime(2026, 8, 21, 18, 0, tzinfo=UTC)


@pytest.fixture
def session_mock() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def clock_mock() -> Mock:
    return Mock(return_value=FIXED_NOW)


@pytest.fixture
def service(session_mock: AsyncMock, clock_mock: Mock) -> TaskService:
    return TaskService(session_mock, clock=clock_mock)


def _make_task(
    *,
    task_id: int = TASK_ID,
    user_id: int = USER_ID,
    title: str = "Buy milk",
    description: str | None = "After work",
    due_at: datetime | None = OLD_DUE_AT,
    is_done: bool = False,
    done_at: datetime | None = None,
) -> Task:
    return Task(
        id=task_id,
        user_id=user_id,
        title=title,
        description=description,
        due_at=due_at,
        is_done=is_done,
        done_at=done_at,
    )


@pytest.mark.asyncio
async def test_create_success_returns_repository_task_and_commits(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_task = _make_task()
    create_mock = AsyncMock(return_value=created_task)
    monkeypatch.setattr(service._tasks, "create_task", create_mock)

    result = await service.create_task(
        user_id=USER_ID,
        title="Buy milk",
        description="After work",
        due_at=NEW_DUE_AT,
    )

    assert result is created_task
    create_mock.assert_awaited_once_with(
        user_id=USER_ID,
        title="Buy milk",
        description="After work",
        due_at=NEW_DUE_AT,
    )
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_repository_error_rolls_back_and_raises_infrastructure_error(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service._tasks,
        "create_task",
        AsyncMock(side_effect=SQLAlchemyError("Database unavailable")),
    )

    with pytest.raises(TaskInfrastructureError):
        await service.create_task(
            user_id=USER_ID,
            title="Buy milk",
            description=None,
            due_at=None,
        )

    session_mock.rollback.assert_awaited_once()
    session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_commit_failure_rolls_back_and_raises_infrastructure_error(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_mock = AsyncMock(return_value=_make_task())
    monkeypatch.setattr(service._tasks, "create_task", create_mock)
    session_mock.commit.side_effect = SQLAlchemyError("Commit failed")

    with pytest.raises(TaskInfrastructureError):
        await service.create_task(
            user_id=USER_ID,
            title="Buy milk",
            description=None,
            due_at=None,
        )

    create_mock.assert_awaited_once()
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_non_empty_returns_user_scoped_tasks_without_transaction(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tasks = [
        _make_task(),
        _make_task(
            task_id=43,
            title="Call dentist",
        ),
    ]
    list_mock = AsyncMock(return_value=tasks)
    monkeypatch.setattr(service._tasks, "list_for_user", list_mock)

    result = await service.list_tasks(user_id=USER_ID)

    assert result == tasks
    list_mock.assert_awaited_once_with(user_id=USER_ID)
    session_mock.commit.assert_not_awaited()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_empty_is_a_successful_result(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    list_mock = AsyncMock(return_value=[])
    monkeypatch.setattr(service._tasks, "list_for_user", list_mock)

    result = await service.list_tasks(user_id=USER_ID)

    assert result == []
    list_mock.assert_awaited_once_with(user_id=USER_ID)
    session_mock.commit.assert_not_awaited()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_database_error_rolls_back_and_raises_infrastructure_error(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    list_mock = AsyncMock(side_effect=SQLAlchemyError("Database unavailable"))
    monkeypatch.setattr(service._tasks, "list_for_user", list_mock)

    with pytest.raises(TaskInfrastructureError):
        await service.list_tasks(user_id=USER_ID)

    list_mock.assert_awaited_once_with(user_id=USER_ID)
    session_mock.rollback.assert_awaited_once()
    session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_success_returns_owner_scoped_task_without_transaction(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task()
    get_mock = AsyncMock(return_value=task)
    monkeypatch.setattr(service._tasks, "get_by_id_for_user", get_mock)

    result = await service.get_task(user_id=USER_ID, task_id=TASK_ID)

    assert result is task
    get_mock.assert_awaited_once_with(task_id=TASK_ID, user_id=USER_ID)
    session_mock.commit.assert_not_awaited()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_none_raises_not_found_without_transaction(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(service._tasks, "get_by_id_for_user", get_mock)

    with pytest.raises(TaskNotFoundError):
        await service.get_task(user_id=USER_ID, task_id=TASK_ID)

    get_mock.assert_awaited_once_with(task_id=TASK_ID, user_id=USER_ID)
    session_mock.commit.assert_not_awaited()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_database_error_rolls_back_and_raises_infrastructure_error(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_mock = AsyncMock(side_effect=SQLAlchemyError("Database unavailable"))
    monkeypatch.setattr(service._tasks, "get_by_id_for_user", get_mock)

    with pytest.raises(TaskInfrastructureError):
        await service.get_task(user_id=USER_ID, task_id=TASK_ID)

    get_mock.assert_awaited_once_with(task_id=TASK_ID, user_id=USER_ID)
    session_mock.rollback.assert_awaited_once()
    session_mock.commit.assert_not_awaited()


def _mock_successful_update(
    service: TaskService,
    monkeypatch: pytest.MonkeyPatch,
    task: Task,
) -> tuple[AsyncMock, AsyncMock]:
    get_mock = AsyncMock(return_value=task)
    update_mock = AsyncMock(return_value=task)
    monkeypatch.setattr(service._tasks, "get_by_id_for_user", get_mock)
    monkeypatch.setattr(service._tasks, "update_task", update_mock)
    return get_mock, update_mock


@pytest.mark.asyncio
async def test_update_ordinary_fields_mutates_and_persists_task(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task(title="Old title", description="Old description")
    get_mock, update_mock = _mock_successful_update(service, monkeypatch, task)

    result = await service.update_task(
        user_id=USER_ID,
        task_id=TASK_ID,
        title="New title",
        description="New description",
        due_at=NEW_DUE_AT,
    )

    assert result is task
    assert (task.title, task.description, task.due_at) == (
        "New title",
        "New description",
        NEW_DUE_AT,
    )
    get_mock.assert_awaited_once_with(task_id=TASK_ID, user_id=USER_ID)
    update_mock.assert_awaited_once_with(task)
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_omitted_fields_remain_unchanged(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task(is_done=True, done_at=OLD_DONE_AT)
    original = (task.title, task.description, task.due_at, task.is_done, task.done_at)
    _mock_successful_update(service, monkeypatch, task)

    result = await service.update_task(user_id=USER_ID, task_id=TASK_ID)

    assert result is task
    assert (task.title, task.description, task.due_at, task.is_done, task.done_at) == original
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_explicit_none_clears_nullable_fields_only(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task(is_done=True, done_at=OLD_DONE_AT)
    _, update_mock = _mock_successful_update(service, monkeypatch, task)

    result = await service.update_task(
        user_id=USER_ID,
        task_id=TASK_ID,
        description=None,
        due_at=None,
    )

    assert result is task
    assert task.description is None
    assert task.due_at is None
    assert task.title == "Buy milk"
    assert task.is_done is True
    assert task.done_at == OLD_DONE_AT
    update_mock.assert_awaited_once_with(task)
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_false_to_true_sets_done_at(
    service: TaskService,
    session_mock: AsyncMock,
    clock_mock: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task(is_done=False, done_at=None)
    _, update_mock = _mock_successful_update(service, monkeypatch, task)

    result = await service.update_task(user_id=USER_ID, task_id=TASK_ID, is_done=True)

    assert result is task
    assert task.is_done is True
    assert task.done_at == FIXED_NOW
    clock_mock.assert_called_once_with()
    update_mock.assert_awaited_once_with(task)
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_true_to_false_clears_done_at(
    service: TaskService,
    session_mock: AsyncMock,
    clock_mock: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task(is_done=True, done_at=OLD_DONE_AT)
    _, update_mock = _mock_successful_update(service, monkeypatch, task)

    await service.update_task(user_id=USER_ID, task_id=TASK_ID, is_done=False)

    assert task.is_done is False
    assert task.done_at is None
    clock_mock.assert_not_called()
    update_mock.assert_awaited_once_with(task)
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_true_to_true_preserves_done_at(
    service: TaskService,
    session_mock: AsyncMock,
    clock_mock: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task(is_done=True, done_at=OLD_DONE_AT)
    _, update_mock = _mock_successful_update(service, monkeypatch, task)

    await service.update_task(user_id=USER_ID, task_id=TASK_ID, is_done=True)

    assert task.is_done is True
    assert task.done_at == OLD_DONE_AT
    clock_mock.assert_not_called()
    update_mock.assert_awaited_once_with(task)
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_false_to_false_keeps_done_at_unset(
    service: TaskService,
    session_mock: AsyncMock,
    clock_mock: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task(is_done=False, done_at=None)
    _, update_mock = _mock_successful_update(service, monkeypatch, task)

    await service.update_task(user_id=USER_ID, task_id=TASK_ID, is_done=False)

    assert task.is_done is False
    assert task.done_at is None
    clock_mock.assert_not_called()
    update_mock.assert_awaited_once_with(task)
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_not_found_stops_before_persistence(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_mock = AsyncMock(return_value=None)
    update_mock = AsyncMock()
    monkeypatch.setattr(service._tasks, "get_by_id_for_user", get_mock)
    monkeypatch.setattr(service._tasks, "update_task", update_mock)

    with pytest.raises(TaskNotFoundError):
        await service.update_task(user_id=USER_ID, task_id=TASK_ID, title="New title")

    get_mock.assert_awaited_once_with(task_id=TASK_ID, user_id=USER_ID)
    update_mock.assert_not_awaited()
    session_mock.commit.assert_not_awaited()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_repository_error_rolls_back_and_raises_infrastructure_error(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task()
    monkeypatch.setattr(service._tasks, "get_by_id_for_user", AsyncMock(return_value=task))
    update_mock = AsyncMock(side_effect=SQLAlchemyError("update failed"))
    monkeypatch.setattr(service._tasks, "update_task", update_mock)

    with pytest.raises(TaskInfrastructureError):
        await service.update_task(user_id=USER_ID, task_id=TASK_ID, title="New title")

    update_mock.assert_awaited_once_with(task)
    session_mock.rollback.assert_awaited_once()
    session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_commit_failure_rolls_back_and_raises_infrastructure_error(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task()
    _, update_mock = _mock_successful_update(service, monkeypatch, task)
    session_mock.commit.side_effect = SQLAlchemyError("commit failed")

    with pytest.raises(TaskInfrastructureError):
        await service.update_task(user_id=USER_ID, task_id=TASK_ID, title="New title")

    update_mock.assert_awaited_once_with(task)
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_success_uses_owner_lookup_and_commits(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task()
    get_mock = AsyncMock(return_value=task)
    delete_mock = AsyncMock()
    monkeypatch.setattr(service._tasks, "get_by_id_for_user", get_mock)
    monkeypatch.setattr(service._tasks, "delete_task", delete_mock)

    await service.delete_task(user_id=USER_ID, task_id=TASK_ID)

    get_mock.assert_awaited_once_with(task_id=TASK_ID, user_id=USER_ID)
    delete_mock.assert_awaited_once_with(task)
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_not_found_stops_before_persistence(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_mock = AsyncMock(return_value=None)
    delete_mock = AsyncMock()
    monkeypatch.setattr(service._tasks, "get_by_id_for_user", get_mock)
    monkeypatch.setattr(service._tasks, "delete_task", delete_mock)

    with pytest.raises(TaskNotFoundError):
        await service.delete_task(user_id=USER_ID, task_id=TASK_ID)

    get_mock.assert_awaited_once_with(task_id=TASK_ID, user_id=USER_ID)
    delete_mock.assert_not_awaited()
    session_mock.commit.assert_not_awaited()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_repository_error_rolls_back_and_raises_infrastructure_error(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task()
    monkeypatch.setattr(service._tasks, "get_by_id_for_user", AsyncMock(return_value=task))
    delete_mock = AsyncMock(side_effect=SQLAlchemyError("delete failed"))
    monkeypatch.setattr(service._tasks, "delete_task", delete_mock)

    with pytest.raises(TaskInfrastructureError):
        await service.delete_task(user_id=USER_ID, task_id=TASK_ID)

    delete_mock.assert_awaited_once_with(task)
    session_mock.rollback.assert_awaited_once()
    session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_commit_failure_rolls_back_and_raises_infrastructure_error(
    service: TaskService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _make_task()
    monkeypatch.setattr(service._tasks, "get_by_id_for_user", AsyncMock(return_value=task))
    delete_mock = AsyncMock()
    monkeypatch.setattr(service._tasks, "delete_task", delete_mock)
    session_mock.commit.side_effect = SQLAlchemyError("commit failed")

    with pytest.raises(TaskInfrastructureError):
        await service.delete_task(user_id=USER_ID, task_id=TASK_ID)

    delete_mock.assert_awaited_once_with(task)
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_awaited_once()
