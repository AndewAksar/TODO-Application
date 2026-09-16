from __future__ import annotations

from datetime import UTC, datetime

import pytest
from services.api_gateway.app.models import Task, User
from services.api_gateway.app.tasks.service import TaskNotFoundError, TaskService
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.integration

FIXED_NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
ORIGINAL_DONE_AT = datetime(2026, 9, 12, 9, 30, tzinfo=UTC)
ORIGINAL_DUE_AT = datetime(2026, 9, 20, 17, 0, tzinfo=UTC)
NEW_DUE_AT = datetime(2026, 9, 21, 18, 30, tzinfo=UTC)


def _fixed_clock() -> datetime:
    return FIXED_NOW


async def _insert_user(
    session: AsyncSession,
    *,
    email: str,
    username: str,
) -> User:
    user = User(email=email, username=username, password_hash="integration-test-hash")
    session.add(user)
    await session.flush()
    return user


async def _insert_task(
    session: AsyncSession,
    *,
    user_id: int,
    title: str,
    description: str | None = "Known task description",
    due_at: datetime | None = ORIGINAL_DUE_AT,
    is_done: bool = False,
    done_at: datetime | None = None,
) -> Task:
    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        due_at=due_at,
        is_done=is_done,
        done_at=done_at,
    )
    session.add(task)
    await session.flush()
    return task


async def test_create_persists_task(
    integration_session_factory: async_sessionmaker,
) -> None:
    # Arrange
    async with integration_session_factory() as arrange_session:
        user = await _insert_user(arrange_session, email="owner-a@example.test", username="owner-a")
        await arrange_session.commit()
        user_id = user.id

    # Act
    async with integration_session_factory() as service_session:
        service = TaskService(service_session, clock=_fixed_clock)
        created = await service.create_task(
            user_id=user_id,
            title="Prepare integration report",
            description="Verify persisted task fields",
            due_at=NEW_DUE_AT,
        )
        task_id = created.id

    # Assert
    async with integration_session_factory() as verification_session:
        stored = await verification_session.get(Task, task_id)
        assert stored is not None
        assert (
            stored.user_id,
            stored.title,
            stored.description,
            stored.due_at,
            stored.is_done,
            stored.done_at,
        ) == (
            user_id,
            "Prepare integration report",
            "Verify persisted task fields",
            NEW_DUE_AT,
            False,
            None,
        )


async def test_list_is_owner_scoped(
    integration_session_factory: async_sessionmaker,
) -> None:
    # Arrange
    async with integration_session_factory() as arrange_session:
        owner_a = await _insert_user(
            arrange_session, email="list-a@example.test", username="list-owner-a"
        )
        owner_b = await _insert_user(
            arrange_session, email="list-b@example.test", username="list-owner-b"
        )
        task_a1 = await _insert_task(arrange_session, user_id=owner_a.id, title="A1")
        task_a2 = await _insert_task(arrange_session, user_id=owner_a.id, title="A2")
        task_b1 = await _insert_task(arrange_session, user_id=owner_b.id, title="B1")
        await arrange_session.commit()
        owner_a_id = owner_a.id
        expected_ids = {task_a1.id, task_a2.id}
        foreign_id = task_b1.id

    # Act
    async with integration_session_factory() as service_session:
        result = await TaskService(service_session, clock=_fixed_clock).list_tasks(
            user_id=owner_a_id
        )

    # Assert
    result_ids = {task.id for task in result}
    assert result_ids == expected_ids
    assert foreign_id not in result_ids


async def test_get_returns_own_task(
    integration_session_factory: async_sessionmaker,
) -> None:
    # Arrange
    async with integration_session_factory() as arrange_session:
        owner = await _insert_user(
            arrange_session, email="get-own@example.test", username="get-own"
        )
        task = await _insert_task(arrange_session, user_id=owner.id, title="Owned task")
        await arrange_session.commit()
        owner_id, task_id = owner.id, task.id

    # Act
    async with integration_session_factory() as service_session:
        result = await TaskService(service_session, clock=_fixed_clock).get_task(
            user_id=owner_id, task_id=task_id
        )

    # Assert
    assert (result.id, result.user_id) == (task_id, owner_id)


async def test_get_hides_foreign_task(
    integration_session_factory: async_sessionmaker,
) -> None:
    # Arrange
    async with integration_session_factory() as arrange_session:
        owner_a = await _insert_user(arrange_session, email="get-a@example.test", username="get-a")
        owner_b = await _insert_user(arrange_session, email="get-b@example.test", username="get-b")
        foreign_task = await _insert_task(
            arrange_session, user_id=owner_b.id, title="Private B task"
        )
        await arrange_session.commit()
        owner_a_id, foreign_task_id = owner_a.id, foreign_task.id

    # Act / Assert
    async with integration_session_factory() as service_session:
        with pytest.raises(TaskNotFoundError):
            await TaskService(service_session, clock=_fixed_clock).get_task(
                user_id=owner_a_id, task_id=foreign_task_id
            )


async def test_update_ordinary_fields_persist(
    integration_session_factory: async_sessionmaker,
) -> None:
    # Arrange
    async with integration_session_factory() as arrange_session:
        owner = await _insert_user(
            arrange_session, email="update@example.test", username="update-owner"
        )
        task = await _insert_task(
            arrange_session,
            user_id=owner.id,
            title="Original title",
            description="Original description",
        )
        await arrange_session.commit()
        owner_id, task_id = owner.id, task.id

    # Act
    async with integration_session_factory() as service_session:
        await TaskService(service_session, clock=_fixed_clock).update_task(
            user_id=owner_id,
            task_id=task_id,
            title="Updated title",
            description="Updated description",
            due_at=NEW_DUE_AT,
        )

    # Assert
    async with integration_session_factory() as verification_session:
        stored = await verification_session.get(Task, task_id)
        assert stored is not None
        assert (stored.title, stored.description, stored.due_at) == (
            "Updated title",
            "Updated description",
            NEW_DUE_AT,
        )


async def test_mark_done_persists_fixed_done_at(
    integration_session_factory: async_sessionmaker,
) -> None:
    # Arrange
    async with integration_session_factory() as arrange_session:
        owner = await _insert_user(
            arrange_session, email="done@example.test", username="done-owner"
        )
        task = await _insert_task(arrange_session, user_id=owner.id, title="Finish task")
        await arrange_session.commit()
        owner_id, task_id = owner.id, task.id

    # Act
    async with integration_session_factory() as service_session:
        await TaskService(service_session, clock=_fixed_clock).update_task(
            user_id=owner_id, task_id=task_id, is_done=True
        )

    # Assert
    async with integration_session_factory() as verification_session:
        stored = await verification_session.get(Task, task_id)
        assert stored is not None
        assert stored.is_done is True
        assert stored.done_at == FIXED_NOW


async def test_mark_not_done_clears_done_at(
    integration_session_factory: async_sessionmaker,
) -> None:
    # Arrange
    async with integration_session_factory() as arrange_session:
        owner = await _insert_user(
            arrange_session, email="reopen@example.test", username="reopen-owner"
        )
        task = await _insert_task(
            arrange_session,
            user_id=owner.id,
            title="Reopen title",
            is_done=True,
            done_at=ORIGINAL_DONE_AT,
        )
        await arrange_session.commit()
        owner_id, task_id = owner.id, task.id

    # Act
    async with integration_session_factory() as service_session:
        await TaskService(service_session, clock=_fixed_clock).update_task(
            user_id=owner_id, task_id=task_id, is_done=False
        )

    # Assert
    async with integration_session_factory() as verification_session:
        stored = await verification_session.get(Task, task_id)
        assert stored is not None
        assert stored.is_done is False
        assert stored.done_at is None


async def test_foreign_update_is_blocked_without_mutation(
    integration_session_factory: async_sessionmaker,
) -> None:
    # Arrange
    async with integration_session_factory() as arrange_session:
        owner_a = await _insert_user(
            arrange_session, email="patch-a@example.test", username="patch-a"
        )
        owner_b = await _insert_user(
            arrange_session, email="patch-b@example.test", username="patch-b"
        )
        foreign_task = await _insert_task(
            arrange_session,
            user_id=owner_b.id,
            title="B original title",
            description="B original description",
        )
        await arrange_session.commit()
        owner_a_id, owner_b_id, task_id = owner_a.id, owner_b.id, foreign_task.id

    # Act / Assert access denial
    async with integration_session_factory() as service_session:
        with pytest.raises(TaskNotFoundError):
            await TaskService(service_session, clock=_fixed_clock).update_task(
                user_id=owner_a_id,
                task_id=task_id,
                title="Unauthorized description",
                description="Unauthorized description",
                due_at=NEW_DUE_AT,
            )

    # Assert non-mutation through a frash session
    async with integration_session_factory() as verification_session:
        stored = await verification_session.get(Task, task_id)
        assert stored is not None
        assert (stored.user_id, stored.title, stored.description, stored.due_at) == (
            owner_b_id,
            "B original title",
            "B original description",
            ORIGINAL_DUE_AT,
        )


async def test_delete_own_task_persists(
    integration_session_factory: async_sessionmaker,
) -> None:
    # Arrange
    async with integration_session_factory() as arrange_session:
        owner = await _insert_user(
            arrange_session, email="delete@example.test", username="delete-owner"
        )
        task = await _insert_task(arrange_session, user_id=owner.id, title="Delete me")
        await arrange_session.commit()
        owner_id, task_id = owner.id, task.id

    # Act
    async with integration_session_factory() as service_session:
        await TaskService(service_session, clock=_fixed_clock).delete_task(
            user_id=owner_id, task_id=task_id
        )

    # Assert
    async with integration_session_factory() as verification_session:
        assert await verification_session.get(Task, task_id) is None


async def test_foreign_delete_is_blocked_without_deletion(
    integration_session_factory: async_sessionmaker,
) -> None:
    # Arrange
    async with integration_session_factory() as arrange_session:
        owner_a = await _insert_user(
            arrange_session, email="delete-a@example.test", username="delete-a"
        )
        owner_b = await _insert_user(
            arrange_session, email="delete-b@example.test", username="delete-b"
        )
        foreign_task = await _insert_task(arrange_session, user_id=owner_b.id, title="Keep B task")
        await arrange_session.commit()
        owner_a_id, owner_b_id, task_id = owner_a.id, owner_b.id, foreign_task.id

    # Act / Assert access denial
    async with integration_session_factory() as service_session:
        with pytest.raises(TaskNotFoundError):
            await TaskService(service_session, clock=_fixed_clock).delete_task(
                user_id=owner_a_id, task_id=task_id
            )

    # Assert non-deletion through a fresh session
    async with integration_session_factory() as verification_session:
        stored = await verification_session.get(Task, task_id)
        assert stored is not None
        assert stored.user_id == owner_b_id
