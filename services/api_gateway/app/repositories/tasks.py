from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api_gateway.app.models import Task


class TaskRepository:
    """Database-access operations for user-owned tasks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_task(
        self,
        *,
        user_id: int,
        title: str,
        description: str | None,
        due_at: datetime | None,
    ) -> Task:
        if not isinstance(user_id, int):
            raise TypeError("user_id must be int")
        if not isinstance(title, str):
            raise TypeError("title must be str")
        if description is not None and not isinstance(description, str):
            raise TypeError("description must be str or None")
        if due_at is not None and not isinstance(due_at, datetime):
            raise TypeError("due_at must be datetime or None")

        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            due_at=due_at,
        )
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)

        return task

    async def list_for_user(self, user_id: int) -> list[Task]:
        if not isinstance(user_id, int):
            raise TypeError("user_id must be int")

        stmt = select(Task).where(Task.user_id == user_id)
        result = await self._session.execute(stmt)

        return list(result.scalars().all())

    async def get_by_id_for_user(
        self,
        *,
        task_id: int,
        user_id: int,
    ) -> Task | None:
        if not isinstance(task_id, int):
            raise TypeError("task_id must be int")
        if not isinstance(user_id, int):
            raise TypeError("user_id must be int")

        stmt = select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
        )
        result = await self._session.execute(stmt)

        return cast(Task | None, result.scalar_one_or_none())

    async def update_task(self, task: Task) -> Task:
        if not isinstance(task, Task):
            raise TypeError("task must be Task")

        await self._session.flush()
        await self._session.refresh(task)

        return task

    async def delete_task(self, task: Task) -> None:
        if not isinstance(task, Task):
            raise TypeError("task must be Task")

        await self._session.delete(task)
        await self._session.flush()
