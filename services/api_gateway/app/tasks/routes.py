from __future__ import annotations

from typing import Annotated, cast

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from services.api_gateway.app.api.deps import get_session
from services.api_gateway.app.auth.dependencies import get_current_user
from services.api_gateway.app.models import User
from services.api_gateway.app.tasks.schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)
from services.api_gateway.app.tasks.service import (
    TaskInfrastructureError,
    TaskNotFoundError,
    TaskService,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

SessionDependency = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    payload: TaskCreateRequest,
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> TaskResponse:
    service = TaskService(session)

    try:
        task = await service.create_task(
            user_id=current_user.id,
            title=payload.title,
            description=payload.description,
            due_at=payload.due_at,
        )
    except TaskInfrastructureError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        ) from exc

    return cast(TaskResponse, TaskResponse.model_validate(task))


@router.get(
    "",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
)
async def get_tasks(
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> list[TaskResponse]:
    service = TaskService(session)

    try:
        tasks = await service.list_tasks(user_id=current_user.id)
    except TaskInfrastructureError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        ) from exc

    return [cast(TaskResponse, TaskResponse.model_validate(task)) for task in tasks]


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def get_task(
    task_id: int,
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> TaskResponse:
    service = TaskService(session)

    try:
        task = await service.get_task(
            user_id=current_user.id,
            task_id=task_id,
        )
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc
    except TaskInfrastructureError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        ) from exc

    return cast(TaskResponse, TaskResponse.model_validate(task))


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_task(
    task_id: int,
    payload: TaskUpdateRequest,
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> TaskResponse:
    service = TaskService(session)
    updates = payload.model_dump(exclude_unset=True)

    try:
        task = await service.update_task(
            user_id=current_user.id,
            task_id=task_id,
            **updates,
        )
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc
    except TaskInfrastructureError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        ) from exc

    return cast(TaskResponse, TaskResponse.model_validate(task))


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_task(
    task_id: int,
    session: SessionDependency,
    current_user: CurrentUserDependency,
) -> Response:
    service = TaskService(session)

    try:
        await service.delete_task(
            user_id=current_user.id,
            task_id=task_id,
        )
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc
    except TaskInfrastructureError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
