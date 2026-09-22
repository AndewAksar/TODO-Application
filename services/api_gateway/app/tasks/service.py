from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from services.api_gateway.app.models import Task
from services.api_gateway.app.repositories.tasks import TaskRepository


class TaskServiceError(Exception):
    """Base task service exception."""


class TaskNotFoundError(TaskServiceError):
    """Raised when a user-owned task cannot be found."""


class TaskInfrastructureError(TaskServiceError):
    """Raised for infrastructure-level task failures."""


class _UnsetType:
    __slots__ = ()


_UNSET = _UnsetType()


def _utc_now() -> datetime:
    return datetime.now(UTC)


class TaskService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._session = session
        self._tasks = TaskRepository(session)
        self._clock = clock

    async def create_task(
        self,
        *,
        user_id: int,
        title: str,
        description: str | None,
        due_at: datetime | None,
    ) -> Task:
        try:
            task = await self._tasks.create_task(
                user_id=user_id,
                title=title,
                description=description,
                due_at=due_at,
            )
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise TaskInfrastructureError("database operation failed") from exc

        return task

    async def list_tasks(self, *, user_id: int) -> list[Task]:
        try:
            return await self._tasks.list_for_user(user_id=user_id)
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise TaskInfrastructureError("database operation failed") from exc

    async def get_task(self, *, user_id: int, task_id: int) -> Task:
        try:
            task = await self._tasks.get_by_id_for_user(
                task_id=task_id,
                user_id=user_id,
            )
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise TaskInfrastructureError("database operation failed") from exc

        if task is None:
            raise TaskNotFoundError("task not found")

        return task

    async def update_task(
        self,
        *,
        user_id: int,
        task_id: int,
        title: str | _UnsetType = _UNSET,
        description: str | None | _UnsetType = _UNSET,
        due_at: datetime | None | _UnsetType = _UNSET,
        is_done: bool | _UnsetType = _UNSET,
    ) -> Task:
        try:
            task = await self._tasks.get_by_id_for_user(
                task_id=task_id,
                user_id=user_id,
            )
            if task is None:
                raise TaskNotFoundError("task not found")

            if not isinstance(title, _UnsetType):
                task.title = title
            if not isinstance(description, _UnsetType):
                task.description = description
            if not isinstance(due_at, _UnsetType):
                task.due_at = due_at

            if not isinstance(is_done, _UnsetType):
                was_done = task.is_done
                task.is_done = is_done
                if not was_done and is_done:
                    task.done_at = self._clock()
                elif was_done and not is_done:
                    task.done_at = None

            task = await self._tasks.update_task(task)
            await self._session.commit()
        except TaskNotFoundError:
            raise
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise TaskInfrastructureError("database operation failed") from exc

        return task

    async def delete_task(self, *, user_id: int, task_id: int) -> None:
        try:
            task = await self._tasks.get_by_id_for_user(
                task_id=task_id,
                user_id=user_id,
            )
            if task is None:
                raise TaskNotFoundError("task not found")

            await self._tasks.delete_task(task)
            await self._session.commit()
        except TaskNotFoundError:
            raise
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise TaskInfrastructureError("database operation failed") from exc
