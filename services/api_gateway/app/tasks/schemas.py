from __future__ import annotations

from typing import Annotated

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    StringConstraints,
    field_validator,
)
from pydantic.json_schema import SkipJsonSchema

TaskTitle = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=255,
        strip_whitespace=True,
    ),
]


class TaskSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaskCreateRequest(TaskSchema):
    title: TaskTitle
    description: str | None = None
    due_at: AwareDatetime | None = None


class TaskUpdateRequest(TaskSchema):
    title: TaskTitle | SkipJsonSchema[None] = None
    description: str | None = None
    due_at: AwareDatetime | None = None
    is_done: bool | SkipJsonSchema[None] = None

    @field_validator("title", "is_done", mode="before")
    @classmethod
    def reject_explicit_null(cls, value: object) -> object:
        if value is None:
            msg = "Field may be omitted, but may not be null."
            raise ValueError(msg)
        return value


class TaskResponse(TaskSchema):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: int
    user_id: int
    title: str
    description: str | None
    is_done: bool
    done_at: AwareDatetime | None
    due_at: AwareDatetime | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
